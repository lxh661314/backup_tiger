





CMDB_HOST_INFORMATION="/api/cmdb/cmdb_host_information"
CMDB_STORAGE_INFORMATION='/api/cmdb/cmdb_storage_information'
BACKUP_HOST_MANAGER = '/api/backup/backup_host_manager'
SYS_ACCOUNT_LOGIN='/api/login/account_login'
BACKUP_DATABASE_MANAGER='/api/backup/backup_database_manager'
BACKUP_FS_MANAGER='/api/backup/backup_fs_manager'
BACKUP_POLICY_MANAGER='/api/backup/backup_policy_manager'
BACKUP_HISTORY_LIST='/api/backup/backup_history_list'
ACCOUNT_LOGIN_API = '/api/auth/login'
ACCOUNT_LOGOUT_API = '/api/auth/logout'
ACCOUNT_LOGIN_INFO = '/api/auth/account_login_info'
BACKUP_POLICY_SCHED_MANAGER = '/api/backup/backup_policy_sched_manager'
ACCOUNT_LOGIN_INFO="/api/auth/account_login_info"
ACCOUNT_CURRENT_USER='/api/auth/account_current_user'


function modalalertdemo(msg, interval=5000){
	    $.Huimodalalert(msg ,interval)
    }


function login_acquire(){
	    var cookie = document.cookie;
	    console.log(cookie);
	    console.log(typeof cookie);
		var re = /login=true/i;
	    var login = cookie.search(re);
		if (login == -1){
		    window.open("/static/login.html", '_self')
		}
	}



function format_timestamp(timestamp) {
        let date = new Date(timestamp * 1000);//时间戳为10位需*1000，时间戳为13位的话不需乘1000
        let Y = date.getFullYear() + '-';
        let M = (date.getMonth()+1 < 10 ? '0'+(date.getMonth()+1) : date.getMonth()+1) + '-';
        let D = date.getDate() + ' ';
        let h = date.getHours() + ':';
        let m = (date.getMinutes() < 10 ? '0'  + date.getMinutes() : date.getMinutes()) + ':';
        let s = date.getSeconds() < 10 ? '0' + date.getSeconds() : date.getSeconds();
        return Y+M+D+h+m+s;
    }
    
function ajaxGet(url){
//不带参数的 ajaxget请求
         var result;
         $.ajax({
            url: url,
            async: false,
            success: function (args) {
                result=args
            },

             error: function(XMLHttpRequest, textStatus, errorThrown) {
                result = XMLHttpRequest.responseText
             },
        });
        return result
        }

function ajaxGet_data(url, data){
//ajax带有参数的ajaxGET请求
        var result;
        $.ajax({
            data: data,
            url: url,
            async: false,
            success: function (args){
                result=args
            },

            error: function(XMLHttpRequest, textStatus, errorThrown) {

                 result = XMLHttpRequest.responseText

             },


        });
        return result
        }   //GET请求

function ajaxPut(url, data, async=false){
//ajax POST请求
        var result;
        $.ajax({
            data:data,
            url:url,
            type:"PUT",
            async:async,
            success:function(msg){
                    result =  msg;
            },

            error: function(XMLHttpRequest, textStatus, errorThrown) {

                result = XMLHttpRequest.responseText
             },

        });
        return result
    }

function ajaxDelete(url, data){
//ajax POST请求
        var result;
        $.ajax({
            data:data,
            url:url,
            type:"DELETE",
            async:false,
            success:function(msg){
                    result =  msg;
            },

            error: function(XMLHttpRequest, textStatus, errorThrown) {
                result = XMLHttpRequest.responseText
                //modalalertdemo(msg);
             },

        });
        return result
    }

function ajaxPost(url, data){
//ajax POST请求
        var result;
        $.ajax({
            data:data,
            url:url,
            type:"POST",
            async:false,
            success:function(msg){
                result =  msg;
            },

            error: function(XMLHttpRequest, textStatus, errorThrown){
                result = XMLHttpRequest.responseText
             },
            
        });
        return result
    }
