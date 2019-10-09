import pymysql
from DBUtils.PooledDB import PooledDB
import sys
import threading
import json
import os

class dbPool(object):
    _instance_lock = threading.Lock()
    def __new__(cls, *args, **kwargs):
        if not hasattr(dbPool, "_instance"):
            with dbPool._instance_lock:
                if not hasattr(dbPool, "_instance"):
                    dbPool._instance = object.__new__(cls)
        return dbPool._instance

    def __init__(self, kwargs):
        self.__dict__.update(kwargs)
        self.Pool = PooledDB(creator=pymysql, mincached=3, maxcached=5,
                             charset="utf8", host=self.host,
                             port=int(self.port),
                             user=self.user, passwd=self.password)
    def getConn(self):
        return self.Pool.connection()


class dbControl:
    def __init__(self, db_pool):
        self._conn = db_pool.getConn()
        self._cursor = self._conn.cursor()
        self.__group = ''
        self.__where = ''
        self.__order = ''
        self.__limit = ''
        self.__set = ''

    def select_database(self, db_name=''):
        self.db_name = db_name.strip()
        return self

    def select_table(self, table_name):
        if self.db_name:
            self.table = '{database}.{table}'.format(database=self.db_name, table=table_name)
        else:
            raise ValueError('will not select database!')
        return self

    def close(self):
        self._cursor.close()
        self._conn.close()

    def clear(self):
        self.__where = ''
        self.__group = ''
        self.__limit = ''
        self.__order = ''
        self.__set = ''

    def execute(self, sql, final="list"):
        if final == "dict":
            self._cursor = self._conn.cursor(pymysql.cursors.DictCursor)
        elif final == "list":
            self._cursor = self._conn.cursor(pymysql.cursors.Cursor)

        try:
            self._cursor.execute(sql)
            result = self._cursor.fetchall()
            return result
        except Exception as e:
            raise ValueError(str(e))
        finally:
            self.clear()

    def get_fields(self):
        fields = []
        sql = 'show fields from %s' % self.table
        try:
            result = self.execute(sql, final="list")
        except Exception as e:
            raise ValueError(str(e))
        else:
            for j in result:
                try:
                    fields.append(j[0].strip())
                except:
                    fields.append(j['Field'])
            return fields

    def get_fields_columns(self):  # 返回表的字段名跟它的注释的字典
        fields = {}
        try:
            sql = "show full fields from %s" % self.table
            result = self.execute(sql, final="list")
        except Exception as e:
            raise ValueError(str(e))
        else:
            for j in result:
                fields[j[0]] = j[-1]
            return fields

    def where(self, kwargs, vague=[], unlike=[]):
        """
          vague 代表哪些字段模糊查询
          unlike 代表哪些字段是用不相等
         都为空 代表没有模糊查询 没有不相等的字段
        """
        if not kwargs:
            self.__where = ''
        else:
            self.__where = 'where '
            argsList = []
            for (k, v) in kwargs.items():
                if not v:
                    continue
                if isinstance(v, (str, int)):
                    if isinstance(v, int):
                        v = str(v)
                    if ';' in v:  ## in or not in
                        if k in unlike:
                            argsList.append('%s not in (%s)' % (k, ','.join(['"%s"' % j for j in v.split(';') if j])))
                        else:
                            argsList.append('%s in (%s)' % (k, ','.join(['"%s"' % j for j in v.split(';') if j])))
                    else:  ##一个普通的字符串
                        if k in vague and k not in unlike:
                            argsList.append('%s like "%s%%"' % (k, v))
                        elif k in vague and k in unlike:
                            argsList.append('%s not like "%s%%"' % (k, v))

                        elif k not in vague and k not in unlike:
                            argsList.append('%s = "%s"' % (k, v))

                        elif k not in vague and k in unlike:
                            argsList.append('%s != "%s"' % (k, v))
                elif isinstance(v, list) and len(v) == 2:
                    if all([v[0], v[1]]):
                        argsList.append('%s >= "%s" and %s <= "%s"' % (k, v[0], k, v[1]))
            self.__where += ' and '.join(argsList)
        return self

    def select(self, fields='*', final='list', distinct=False):
        case = fields
        if any([isinstance(fields, list) or isinstance(fields, tuple)]):
            if distinct:
                case = 'distinct ' + ','.join(fields)
            else:
                case = ','.join(fields)

        elif isinstance(fields, str):
            if distinct:
                case = ' distinct ' + fields
            else:
                case = fields

        sql = 'select {case} from {table} {where} {group} {order} {limit}'.format(case=case,
                                                                                  table=self.table,
                                                                                  where=self.__where,
                                                                                  group=self.__group,
                                                                                  order=self.__order,
                                                                                  limit=self.__limit)
        print(sql)
        return self.execute(sql, final=final)

    def delete(self):
        sql = 'delete from {table} {where}'.format(table=self.table, where=self.__where)
        print(sql)
        try:
            self.execute(sql)
        except Exception as e:
            raise ValueError(str(e))
        else:
            self.commit()
            return 1
        finally:
            self.clear()

    def update(self):
        sql = 'update {table} {set} {where}'.format(table=self.table, set=self.__set, where=self.__where)
        print(sql)
        try:
            self.execute(sql)
        except Exception as e:
            raise ValueError(str(e))
        else:
            self.commit()
            return 1
        finally:
            self.clear()

    def commit(self):
        self._conn.commit()

    def group(self, group=[]):
        if group:
            self.__group = 'group by {case}'.format(case=', '.join(group))
        return self

    def set(self, kwargs):
        if not kwargs:
            self.__set = ''
        else:
            self.__set = 'set '
            argsList = []
            for (k, v) in kwargs.items():
                argsList.append('%s="%s"' % (k, v))
            self.__set += ','.join(argsList)
        return self

    def order(self, order=[], seq='desc'):
        if not isinstance(order, list):
            raise TypeError('order args must be a list!')
        if not order:
            self.__order = ''
        else:
            self.__order = 'order by' + ' ' + ', '.join(order) + ' ' + seq
        return self

    def limit(self, start='', limit=''):
        if all([not start, not limit]):
            self.__limit = ''
        elif all([not start, limit]):
            self.__limit = 'limit %s' % limit
        else:
            self.__limit = 'limit %s, %s' % (start, limit)
        return self

    def add(self, data=[]):
        #        '''
        #         向表中添加数据
        #        插入的数据格式 [{k: v},{k:v},{k:v}]
        #        [[3, 4, 5], [1, 2, 3], [1, 2, 3]]
        #        '''
        if not data or not isinstance(data, (list, tuple)):
            raise TypeError('insert data type error!')
        fields = self.get_fields()  ##目标表的字段
        value_list = []
        if isinstance(data[0], dict):
            for x in data:
                value = []
                for j in fields:
                    value.append(x.get(j, 0))
                tuple_value = tuple(value)
                value_list.append(tuple_value)

        if isinstance(data[0], list) or isinstance(data[0], tuple):
            value_list = [list(i) + [''] * (len(fields) - len(i)) if len(fields) > len(i) else list(i)[0:len(fields)]
                          for i in data]
            value_list = map((lambda x: tuple(x)), value_list)
        args = []
        for j in value_list:
            args.append('(' + ','.join(['"%s"'] * len(j)) % tuple(j) + ')')
        sql = '''replace into {table}({field}) values {value}'''.format(table=self.table,
                                                                        field=','.join(fields),
                                                                        value=','.join(args)
                                                                        )

        try:
            self.execute(sql)
        except Exception as e:
            raise ValueError(str(e))
        else:
            self.commit()
            return 1

    def innerjoinSelect(self, joindb = "", jointable="", fields={}, common=[], diff={}):
        if fields:
            fieldList = []
            for (k, v) in fields.items():
                for j in v:
                    tmp = '%s.%s'%(k, j)
                    fieldList.append(tmp)
            selectField = ','.join(fieldList)

        if common:
            where = []
            commonList = []
            for j in common:
                tmp = '%s.%s = %s.%s' %(self.table,j,jointable, j)
                commonList.append(tmp)
            commonString = ' and '.join(commonList)
            where.append(commonString)

        if diff:
            diffList = []
            for (k, v) in diff.items():
                for (m, n) in v.items():
                    tmp = '%s.%s = %s' %(k, m, n)
                    diffList.append(tmp)
            diffString = ' and '.join(diffList)
            where.append(diffString)

        if not where:
            self.__where = ''
        else:
            self.__where = 'where %s ' %(' and '.join(where))

        sql = 'select {field} from {table} inner join {joindb}.{jointable} {where} {group} {order} {limit}'.format(field=selectField,
                                                                                                                   table=self.table,
                                                                                                                   joindb=joindb,
                                                                                                                   jointable=jointable,
                                                                                                                   where=self.__where,
                                                                                                                   group=self.__group,
                                                                                                                   order=self.__order,
                                                                                                                   limit=self.__limit
                                                                                                                   )
        #print(sql)

        try:
            result = self.execute(sql)
        except Exception as e:
            raise ValueError(str(e))
        else:
            return result
        finally:
            self.clear()


