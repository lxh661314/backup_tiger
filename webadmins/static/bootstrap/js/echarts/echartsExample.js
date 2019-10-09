$(document).ready(function() {
    var myChart;
    var domCode = document.getElementById('sidebar-code');
    var domGraphic = document.getElementById('graphic');
    var domMain = document.getElementById('main');
    var domMessage = document.getElementById('wrong-message');
    var iconResize = document.getElementById('icon-resize');
    var needRefresh = false;

    var enVersion = location.hash.indexOf('-en') != -1;
    var hash = location.hash.replace('-en', '');
    hash = hash.replace('#', '') || (needMap() ? 'default' : 'macarons');
    hash += enVersion ? '-en' : '';

    var curTheme;

    function requireCallback(ec, defaultTheme) {
        require(['js/echarts/theme/macarons'], function (tarTheme) {
            curTheme = tarTheme;
            echarts = ec;
        })
    }

    function refreshTheme() {
        myChart.hideLoading();
        myChart.setTheme(curTheme);
    }

    function autoResize() {
        if ($(iconResize).hasClass('glyphicon-resize-full')) {
            focusCode();
            iconResize.className = 'glyphicon glyphicon-resize-small';
        }
        else {
            focusGraphic();
            iconResize.className = 'glyphicon glyphicon-resize-full';
        }
    }

    function focusCode() {
        domCode.className = 'col-md-8 ani';
        domGraphic.className = 'col-md-4 ani';
    }

    function focusGraphic() {
        if (needRefresh) {
            myChart.showLoading();
            init();
        }
    }

    function refresh(isBtnRefresh) {
        if (isBtnRefresh) {
            needRefresh = true;
            focusGraphic();
            return;
        }
        needRefresh = false;
        if (myChart && myChart.dispose) {
            myChart.dispose();
        }
        //console.log(editor.doc.getValue());
        myChart = echarts.init(domMain, curTheme);
        window.onresize = myChart.resize;
        //(new Function(editor.doc.getValue()))();
        myChart.setOption(option, true);
        var ecConfig = require('echarts/config');
        console.log(ecConfig);
        myChart.on(ecConfig.EVENT.CLICK, focus);
    }

    function focus(param) {
        var data = param.data;
        var links = option.series[0].links;
        var nodes = option.series[0].nodes;
        if (
            data.source !== undefined
            && data.target !== undefined
        ) { //点击的是边
            var sourceNode = nodes.filter(function (n) {
                return n.name == data.source
            })[0];
            var targetNode = nodes.filter(function (n) {
                return n.name == data.target
            })[0];
            console.log("选中了边 " + sourceNode.name + ' -> ' + targetNode.name + ' (' + data.weight + ')');
        } else { // 点击的是点
            console.log("选中了" + data.name + '(' + data.value + ')');
            //setTimeout(refresh, 100);
            gotoDetails(data.name);
        }
    }

    function needMap() {
        var href = location.href;
        return href.indexOf('map') != -1
            || href.indexOf('mix3') != -1
            || href.indexOf('mix5') != -1
            || href.indexOf('dataRange') != -1;

    }

    var echarts;

// for echarts online home page
    require.config({
        paths: {
            echarts: './js/echarts'
        }
    });

    var isExampleLaunched;

    function launchExample() {
        if (isExampleLaunched) {
            return;
        }
        // 按需加载
        isExampleLaunched = 1;
        require(
            [
                'echarts',
                'echarts/chart/line',
                'echarts/chart/bar',
                'echarts/chart/scatter',
                'echarts/chart/k',
                'echarts/chart/pie',
                'echarts/chart/radar',
                'echarts/chart/force',
                'echarts/chart/chord',
                'echarts/chart/gauge',
                'echarts/chart/funnel',
                'echarts/chart/eventRiver',
                'echarts/chart/venn',
                'echarts/chart/treemap',
                'echarts/chart/tree',
                'echarts/chart/wordCloud',
                'echarts/chart/heatmap',
                needMap() ? 'echarts/chart/map' : 'echarts'
            ],
            requireCallback
        );
    }

    option = {
        title: {
            text: 'Docker集群',
            subtext: '数据来自顺丰Docker云平台',
            x: 'right',
            y: 'bottom'
        },
        tooltip: {
            trigger: 'item'
        },
        toolbox: {
            show: true,
            feature: {
                restore: {show: true},
                magicType: {show: true, type: ['force', 'chord']},
                saveAsImage: {show: true}
            }
        },
        series: [
            {
                type: 'force',
                name: "详细信息:",
                ribbonType: false,
                itemStyle: {
                    normal: {
                        label: {
                            show: true,
                            textStyle: {
                                color: '#333'
                            }
                        },
                        nodeStyle: {
                            brushType: 'both',
                            borderColor: 'rgba(255,215,0,0.4)',
                            borderWidth: 2
                        }
                    },
                    emphasis: {
                        label: {
                            show: false
                            // textStyle: null      // 默认使用全局文本样式，详见TEXTSTYLE
                        },
                        nodeStyle: {
                            //r: 30
                        },
                        linkStyle: {}
                    }
                },
                useWorker: false,
                minRadius : 1,
                maxRadius : 100,
                roam: 'move',
                gravity: 1.1,
                scaling: 1.1,
                nodes: [],
                links: []
            },

        ]
    };
    function createNodeForMarathon(nodeObj,nodes,value,index)
    {
        if(undefined==nodeObj) return;
        var opt = {};
        for(var i=0;i<nodeObj.length;i++)
        {
            var lable = nodeObj[i].marathon_path + "\n" + nodeObj[i].marathon_name+ "\n" +"(主)";
            var name = nodeObj[i].marathon_name+ "\n" +"(主)";
            opt["category"] = index;
            opt["name"] = name;
            opt["value"] = value;
            opt["label"] = lable;
            nodes.push(opt);
        }
        return opt.name;
    }

    function createNodeForMarathonTraffic(marathonMasterName,nodeObj,nodes,links,value,index)
    {
        if(undefined==nodeObj) return;
        for(var i=0;i<nodeObj.length;i++)
        {
            var lable = nodeObj[i].marathon_path + "\n" + nodeObj[i].marathon_name;
            var name = nodeObj[i].marathon_name;
            var opt = {},link={};
            opt["category"] = index;
            opt["name"] = name;
            opt["value"] = value;
            opt["label"] = lable;
            nodes.push(opt);
            link["source"] = marathonMasterName;
            link["target"] = name;
            link["weight"] = index;
            links.push(link);
        }
    }

    function createNodeForMaster(marathonMasterName,nodeObj,nodes,links,value,index)
    {
        if(undefined==nodeObj) return;
        var opt = {};
        for(var i=0;i<nodeObj.length;i++)
        {
            var lable = nodeObj[i].cluster_name + "\nmesos-" + nodeObj[i].master_name;
            var name = nodeObj[i].master_name;
            var link={};
            opt["category"] = index;
            opt["name"] = name;
            opt["value"] = value;
            opt["label"] = lable;
            nodes.push(opt);
            link["source"] = name;
            link["target"] = marathonMasterName;
            link["weight"] = index;
            links.push(link);
        }
        return opt.name;
    }

    function createNodeForSlave(mesosMasterName,nodeObj,nodes,links,value,index)
    {
        if(undefined==nodeObj) return;
        for(var i=0;i<nodeObj.length;i++)
        {
            var lable = nodeObj[i].tenant + "\n" + nodeObj[i].slave_name;
            var name = nodeObj[i].slave_name;
            var opt = {};
            var link={};
            opt["category"] = index;
            opt["name"] = name;
            opt["value"] = value;
            opt["label"] = lable;
            nodes.push(opt);
            link["source"] = name;
            link["target"] = mesosMasterName;
            link["weight"] = index;
            links.push(link);
        }
    }
    function gotoDetails(name)
    {
        var names = name.split("-");
        var mesos_path=names[0];
        if(mesos_path!="mesos") return;
        var cluster_name=names[1];
        var url = "/v1/fbox/mesos/cluster/"+cluster_name;
        ajaxGet(url, {}, function (result) {
            var nodes = [],links=[];
            var marathonMasterName = createNodeForMarathon(result.marathon.marathon,nodes,50,1);
            createNodeForMarathonTraffic(marathonMasterName,result.marathon.marathon_traffic,nodes,links,50,2);
            var mesosMasterName =createNodeForMaster(marathonMasterName,result.master,nodes,links,50,3);
            createNodeForSlave(mesosMasterName,result.slave,nodes,links,50,4);
            option.series[0].nodes = nodes;
            option.series[0].links = links;
            console.log(JSON.stringify(nodes));
            console.log(JSON.stringify(links));
            refresh();
        })
    }
    function init() {
        launchExample();
        //初始化node
        var url = "/v1/fbox/mesos/cluster";
        ajaxGet(url, {}, function (result) {
            var nodes = [];
            for (var i = 0; i < result.length; i++) {
                var name = result[i].mesos_path + "-" + result[i].cluster_name;
                var lable = result[i].note;
                var opt = {};
                opt["category"] = i;
                opt["name"] = name;
                opt["value"] = 50;
                opt["label"] = lable;
                nodes.push(opt);
            }
            option.series[0].nodes = nodes;
            setTimeout(refresh, 1000);
        })
    }
    $("#refresh").bind("click",function(){
         refresh(true);
    })
    init();
});