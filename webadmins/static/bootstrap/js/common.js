var base="http://10.202.27.1:5656";
function startLoading() {
/*	layer.load(2, {
		shade: [0.1,'#000']
	});*/
};
//构造JSON对象给菜单管理
function menu_json(name,href,parent_name){
    this.name=name;
    this.href=href;
    this.parent_name=parent_name;
}
function get_zone_appid(appid){
    var name_array = appid.split('-');

    return name_array[name_array.length-1]
}

function get_pure_appid(appid) {
    var name_array = appid.split('-');
    var pure_appid = [];

    for(var i= 0; i < name_array.length-1; i++){
        pure_appid.push(name_array[i])
    }
    return pure_appid.join('-')
}

function ajax_load_options(option_type, object){

    ajaxGet('/v1/fbox/utils/options/' + option_type, "", function (data) {
        html_content = []
        $.each(data, function (index, dt) {
            html_content.push('<option value="'+ dt.value +'">' + dt.display_name +'</option>' )
        });
        $(object).html(html_content.join(''))
    })
}


String.prototype.startWith=function(s){

if(s==null||s==""||this.length==0||s.length>this.length) return false;

if(this.substr(0,s.length)==s){
    return true}

else{
    return false;
}
};

function toYYYYMMDD(date) {  
    var y = date.getFullYear();  
    var m = date.getMonth() + 1;  
    m = m < 10 ? '0' + m : m;  
    var d = date.getDate();  
    d = d < 10 ? ('0' + d) : d;  
    return y + '-' + m + '-' + d;  
};

function toHHMM(date) {
    var h = date.getHours();
    var minute = date.getMinutes();
    minute = minute < 10 ? ('0' + minute) : minute;
    return  h+':'+minute;
};

function endLoading() {
/*	layer.closeAll("loading");*/
};

/*左边框占满屏幕*/
$(function() {
	var ht=$("html").height();
	$(".left_body").css("height",ht);
});
function neverNull(_mydata){
	if(_mydata == null) return "无";
	if(_mydata == "") return "无";
	return _mydata;
}

function msg_success(msg) {
	// layer.msg(msg, {
	// 	icon : 1,
	// 	time : 1000,
	// 	offset : "150px"
	// });
	if(msg!=null&&msg!="")
		toastr.success('', msg);
}

function msg_box(msg) {
	// layer.msg(msg, {
	// 	icon : 1,
	// 	time : 1000,
	// 	offset : "150px"
	// });
	if(msg!=null&&msg!="")
		toastr.success('', msg);
}

function msg_success(msg, callback) {
	// layer.msg(msg, {
	// 	icon : 1,
	// 	time : 1000,
	// 	offset : "150px"
	// }, callback);
	if(msg!=null&&msg!="")
		toastr.success('', msg);
	callback();
}
function keyboard_commit(keycode,callback) {
	document.onkeydown = function (e) {
		var theEvent = window.event || e;
		var code = theEvent.keyCode || theEvent.which;
		if (code == keycode) {
			callback();
		}
	}
}
function msg_error(msg) {
	// layer.alert(msg, {
	// 	icon : 2,
	// 	offset : "150px"
	// });
	toastr.error(msg);
}


function msg_confirm(msg, callback) {
    var len = $("#dialog_modal").length;
    var len2 = $(".modal-backdrop").length;
    if(len>0)
    {
        $("#dialog_modal").remove();
    }
    if(len2>0)
    {
        $(".modal-backdrop").remove();
    }
    var dialog='<div class="modal fade" id="dialog_modal" >';
    dialog=dialog+'<div class="modal-dialog" style="width: 400px">';
    dialog=dialog+'<div class="modal-content">';
    dialog=dialog+'<div class="modal-header">';
    dialog=dialog+'<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>';
    dialog=dialog+'<h4 class="modal-title" style="color: #252F3D;">温馨提示</h4>';
    dialog=dialog+'</div>';
    dialog=dialog+'<div class="modal-body">';
    dialog=dialog+'<fieldset>';
    dialog=dialog+'<div class="info">';
    dialog=dialog+'<div class="item">';
    dialog=dialog+'<div class="control-label">';
    dialog=dialog+msg;
    dialog=dialog+'</div>';
    dialog=dialog+'</div>';
    dialog=dialog+'</div>';
    dialog=dialog+'</fieldset>';
    dialog=dialog+'</div>';
    dialog=dialog+'<div class="modal-footer">';
    dialog=dialog+'<button type="button" class="btn btn-default" data-dismiss="modal">取消</button>';
    dialog=dialog+'<button type="button" class="btn btn-primary btn-sm" id="dialog_modal_btn">确认</button>';
    dialog=dialog+'</div>';
    dialog=dialog+'</div>';
    dialog=dialog+'</div>';
    dialog=dialog+'</div>';
    $(document.body).append(dialog);
    $('#dialog_modal').modal({
    backdrop: 'static',
    keyboard: false });
    $("#dialog_modal").modal("show");
    $("#dialog_modal_btn").bind("click",function(){
        $("#dialog_modal").modal("hide");
        callback();
    });
	// layer.confirm(msg, {
	// 	icon : 3,
	// 	offset : "150px"
	// }, function(index) {
	// 	layer.close(index);
	// 	callback();
	// });
}
function ajaxPost(url, data, callback, errcallback) {
	this.ajaxPrivate("POST", url, data, callback,errcallback);
}

function ajaxGet(url, data, callback) {
	this.ajaxPrivate("GET", url, data, callback);
}


function ajaxSyncGet(url, data, callback) {
	this.ajaxSyncPrivate("GET", url, data, callback);
}

function ajaxDelete(url, data, callback, errcallback) {
	this.ajaxPrivate("DELETE", url, data, callback, errcallback);
}

function ajaxPut(url, data, callback) {
	this.ajaxPrivate("PUT", url, data, callback);
}

function ajaxPrivate(type, url, data, callback, errcallback) {
/*	 var flag = url.indexOf("http");
	 if (flag != 0) {
	 	url = base + url;
	 }*/
	$.ajax({
		beforeSend:startLoading,
		complete:endLoading,
		type : type,
		url : url,
		data : data, 
		dataType : "json",
		contentType: "application/json; charset=utf-8",
        xhrFields: {
            withCredentials: true
		},
		success : function(result) {
			//console.log(JSON.stringify(result))
			if (result.status == "SUCCESS") { 
				callback(result.data);
			} else {
			    stop_spin();
				if (result.message != null && result.message != "") {
					msg_error(result.message);
				} else if(result.status =='FAILED' || result.status =='failed'){
				    return;
                } else {
					msg_error(result.status);
				}

                if (errcallback != undefined){
                    errcallback()}
			}
		},  
		error : function(msg) {
		    stop_spin();
			var text = msg.responseText;
			// console.log(msg);
			// if(text.length>2000||text.length==0)
			// 	window.location.href="跳转登陆页面";
			// else
				msg_error(msg.responseText);
            if (errcallback != undefined){
                errcallback()
            }
		}
	});
}



function ajaxSyncPrivate(type, url, data, callback) {
/*	 var flag = url.indexOf("http");
	 if (flag != 0) {
	 	url = base + url;
	 }*/
	$.ajax({
		beforeSend:startLoading,
		complete:endLoading,
		type : type,
		url : url,
		data : data,
		dataType : "json",
		contentType: "application/json; charset=utf-8",
        async : false,
        xhrFields: {
            withCredentials: true
		},
		success : function(result) {
			//console.log(JSON.stringify(result))
			if (result.status == "SUCCESS") {
				callback(result.data);
			} else {
				if (result.message != null && result.message != "") {
					msg_error(result.message);
				} else {
					msg_error(result.status);
				}
			}
		},
		error : function(msg) {
			var text = msg.responseText;
			// console.log(msg);
			// if(text.length>2000||text.length==0)
			// 	window.location.href="跳转登陆页面";
			// else
				msg_error(msg.responseText);
		}
	});
}


function getQueryString(name) {
	var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)", "i");
	var r = window.location.search.substr(1).match(reg);
	if (r != null) return JavaScriptEncode( unescape(decodeURI(r[2])) );
	return null;
}

//使用“\”对特殊字符进行转义，除数字字母之外，小于127使用16进制“\xHH”的方式进行编码，大于用unicode（非常严格模式）。
var JavaScriptEncode = function(str){

    var hex=new Array('0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f');

    function changeTo16Hex(charCode){
        return "\\x" + charCode.charCodeAt(0).toString(16);
    }

    function encodeCharx(original) {

        var found = true;
        var thecharchar = original.charAt(0);
        var thechar = original.charCodeAt(0);
        switch(thecharchar) {
            case '\n': return "\\n"; break; //newline
            case '\r': return "\\r"; break; //Carriage return
            case '\'': return "\\'"; break;
            case '"': return "\\\""; break;
            case '\&': return "\\&"; break;
            case '\\': return "\\\\"; break;
            case '\t': return "\\t"; break;
            case '\b': return "\\b"; break;
            case '\f': return "\\f"; break;
            case '/': return "\\x2F"; break;
            case '<': return "\\x3C"; break;
            case '>': return "\\x3E"; break;
            default:
                found=false;
                break;
        }
        if(!found){
            return original;
        }
    }

    var preescape = str;
    var escaped = "";
    var i=0;
    for(i=0; i < preescape.length; i++){
        escaped = escaped + encodeCharx(preescape.charAt(i));
    }
    return escaped;
}

function getUser(){
	$.ajax({
		url:"/v1/auth/get_user",
		type: 'get',
		dataType: 'json',
		async: false,
		success: function (res) {
		     var tohtml='login.html';
		    if(res.data.iscas=='yes'){
		        tohtml = 'index.html';
            }
			if (res.status == "SUCCESS"){
				if (res.data.status == "login"){
				    //显示导航栏的用户名
					$("#login_user").text(res.data.user_name);
					$("#login_id").text(res.data.user);
                    //删除导航栏不需要显示的部分
                    if(res.data.admin!=1){//平台管理员直接显示全部导航栏
                        //----------------------------同步导航栏和数据库的内容---------------------
                        var menu_content = [];
                        var span_collection = $("#side-menu").find("span.nav-label");
                        span_collection.each(function(k1,v1){
                            menu_content.push(new menu_json($(v1).text(),$(v1).parent().attr('name'),'-'));
                            var children = $(v1).parent().next();
                            if(children.is('ul')){
                                children.find('a').each(function () {
                                    menu_content.push(new menu_json($(this).text(),$(this).attr('name'),$(v1).text()));
                                });
                            }
                        });
                        ajaxPost('/v1/fbox/menuManager/',JSON.stringify(menu_content),function (res) {
                            var parent_menu = $("#side-menu").find("span.nav-label");
                            var child_menu = $("#side-menu").find("a");
                            $(res).each(function(){
                                //没有href，说明是一级菜单
                                if(this.name=='#'){
                                    parent_menu.filter("span:contains('"+this.name+"')").parent().parent().remove();
                                //二级菜单的删除方法
                                }else{
                                    child_menu.filter("a:contains('"+this.name+"')").parent().remove();
                                }
                            })
                        });
                    }
                }
                else{
                    window.location.href = tohtml
                }
			}
			else{
				window.location.href = tohtml
			}
		},
		error: function () {
			window.location.href = 'login.html'
		}
	});
}

function initNav()
{
    var nav="";
    nav = nav+'<nav class="navbar-default navbar-static-side" role="navigation">';
    nav = nav+'   <div class="sidebar-collapse">';
    nav = nav+'       <ul class="nav metismenu" id="side-menu">';
    nav = nav+'           <li class="nav-header">';
    nav = nav+'               <div class="dropdown profile-element"> <span>';
    nav = nav+'                       <a href="landing.html"><img alt="image" class="img-rounded" src="img/logo_title.png" />';
    nav = nav+'                        </a></span>';
    nav = nav+'                   <a data-toggle="dropdown" class="dropdown-toggle" href="#">';
    nav = nav+'                       <span class="clear"> <span class="block m-t-xs"> <strong class="font-bold" id = "login_user">未登录</strong>';
    nav = nav+'                       <strong class="font-bold" id = "login_id" hidden>未登录</strong>';
    nav = nav+'                        </span> <span class="text-muted text-xs block">丰箱FBox平台 <b class="caret"></b></span> </span> </a>';
    nav = nav+'                   <ul class="dropdown-menu animated fadeInRight m-t-xs">';
    nav = nav+'                       <li><a href="#" onclick="logout()">注销</a></li>';
    nav = nav+'                   </ul>';
    nav = nav+'               </div>';
    nav = nav+'               <div class="logo-element">';
    nav = nav+'                   FBox';
    nav = nav+'               </div>';
    nav = nav+'           </li>';
    nav = nav+'           <li id="indexLabel">';
    nav = nav+'               <a name="index_content.html"><i class="fa fa-bar-chart-o"></i> <span class="nav-label">DashBoard</span>  </a>';
    nav = nav+'           </li>';
    nav = nav+'           <li id="createLabel">';
    nav = nav+'               <a name="create.html"><i class="fa fa-plus-square-o"></i> <span class="nav-label">应用创建</span></a>';
    nav = nav+'           </li>';
    nav = nav+'           <li id="appLabel">';
    nav = nav+'               <a name="#"><i class="fa fa-tasks"></i> <span class="nav-label">应用管理</span><span class="fa arrow"></span></a>';
    nav = nav+'               <ul class="nav nav-second-level collapse">';
    nav = nav+'                   <li id="app_managerLabel"><a name="app_manager.html">应用管理</a></li>';
    nav = nav+'                   <li id="ha_managerLabel"><a name="ha_manager.html">负载均衡</a></li>';
    nav = nav+'                   <li id="app_monitorLabel"><a name="app_monitor.html">应用监控</a></li>';
    nav = nav+'                   <li id="app_ipLabel"><a name="app_ip.html">IP管理</a></li>';
    nav = nav+'               </ul>';
    nav = nav+'           </li>';
    nav = nav+'           <li id="mesosLabel">';
    nav = nav+'               <a name="#"><i class="fa fa-cubes"></i> <span class="nav-label">平台管理</span><span class="fa arrow"></span></a>';
    nav = nav+'               <ul class="nav nav-second-level collapse">';
    nav = nav+'                   <li id="clusterLabel"><a name="cluster.html">集群管理</a></li>';
    nav = nav+'                   <li id="zookeeperLabel"><a name="zookeeper.html">ZooKeeper管理</a></li>';
    nav = nav+'                   <li id="marathonLabel"><a name="marathon.html">Marathon管理</a></li>';
    nav = nav+'                   <li id="masterLabel"><a name="master.html">Mesos Master管理</a></li>';
    nav = nav+'                   <li id="slaveLabel"><a name="slave.html">Mesos Slave管理</a></li>';
    nav = nav+'                   <li id="container_infoLabel"><a name="container_info.html">容器信息管理</a></li>';
    nav = nav+'                   <li id="image_menager"><a name="image_menager.html">镜像信息管理</a></li>';
    nav = nav+'                   <li id="fileServerLabel"><a name="fileServer.html">文件服务器管理</a></li>';
    nav = nav+'                   <li id="announceLabel"><a name="announce.html">信息发布</a></li>';
    nav = nav+'                   <li id="abnormalLabel"><a name="abnormal.html">异常管理</a></li>';
    nav = nav+'                   <li><a name="menu_manager.html">菜单管理</a></li>';
    nav = nav+'                   <li><a name="personal_config.html">个性化配置管理</a></li>';
    nav = nav+'               </ul>';
    nav = nav+'           </li>';
    nav = nav+'           <li id="groupLabel">';
    nav = nav+'               <a name="group_manager.html"><i class="fa fa-user"></i> <span class="nav-label">组管理</span>  </a>';
    nav = nav+'           </li>';
    nav = nav+'           <li id="operationsLabel">';
    nav = nav+'               <a name="operations.html"><i class="fa fa-flask"></i> <span class="nav-label">操作记录</span></a>';
    nav = nav+'           </li>';
    nav = nav+'           <li id="faqLabel">';
    nav = nav+'              <a name="#"><i class="fa fa-file-text-o"></i> <span class="nav-label">文档</span><span class="fa arrow"></span></a>';
    nav = nav+'              <ul class="nav nav-second-level collapse">';
    nav = nav+'                   <li id="guideLabel"><a href="resource/guide.pdf" name="resource/guide.pdf" target="_blank">使用指南</a></li>';
    nav = nav+'                   <li id="apiLabel"><a name="api.html">API文档</a></li>';
    nav = nav+'               </ul>';
    nav = nav+'           </li>';
    nav = nav+'       </ul>';
    nav = nav+'   </div>';
    nav = nav+'</nav>';
    $("#navbar").html(nav);
    var key = $("#frame_content").attr('src');
    //让菜单展开
    $("#navbar").find("a[name='"+key+"']").parent().attr("class","active");
    var parent_menu = $("#navbar").find("a[name='"+key+"']").parent().parent().parent().first();
    if(parent_menu.is('li'))
        parent_menu.attr("class","active");

    getUser();
}


var role_desc = {0: '只读用户',
                 1: '发布用户',
                 2: '管理用户',
                 3: '超级用户'};

$(document).ready(function() {
    ifram_jump();
});

function logout() {
    var url="/v1/auth/logout";
    var data={};
    ajaxGet(url, data, function (result) {
        if(isNaN(parseInt(window.location.port))) {
            window.location.href = 'https://' + window.location.host + '/portal/login.html'
        }else{
            if(result["iscas"]=='yes') {
                var logouturl = 'http://' + window.location.host + '/cas/logout';
                $("#casframe").attr("src",logouturl);
                parent.caslogout();
            }else{
                window.location.href = 'http://' + window.location.host + '/portal/login.html'
            }
        }
    });
};
//判断json对象是否为数字，true则是数字，false则有的值不是数字
function isNaNJson(json_obj){
    for(var key in json_obj){
        if(isNaN(json_obj[key]))
            return false;
    }
    return true;
}
//=======================================全屏转菊花=============================================
function start_spin(){

    var width = document.body.clientWidth;
    var height = document.body.clientHeight;
    var posistion = height/2 - 100;
    var background = "<div id='shade' style='opacity:0.50;background-color:white;z-index:9999999999;position: fixed;width: "+width+"px;height: "+height+"px;'>" +
        "<div class='sk-spinner sk-spinner-rotating-plane' style='margin-top:"+posistion+"px;height: 100px;width: 100px;'></div></div>";
    $("body").prepend(background);
}
function stop_spin(){
    $("#shade").remove();
}
//=================================================================================================
function ifram_jump(){
    $("#side-menu").find("a[name!='#']").click(function () {
        $("#frame_content").attr('src',this.name);
        $("#side-menu").find(".active").removeClass('active');
        //让菜单展开
        $("#navbar").find("a[name='"+this.name+"']").parent().attr("class","active");
        var parent_menu = $("#navbar").find("a[name='"+this.name+"']").parent().parent().parent().first();
        if(parent_menu.is('li'))
            parent_menu.attr("class","active");

        $.ajax({
		url:"/v1/auth/get_user",
		type: 'get',
		dataType: 'json',
		async: false,
		success: function (res) {
		    var tohtml='login.html';
		    if(res.data.iscas=='yes'){
		        tohtml = 'index.html';
            }
			if (res.status == "SUCCESS"){
				if (res.data.status == "login")
				    return;
                else{
                    window.location.href = tohtml
                }
			}
			else{
				window.location.href = tohtml
			}
		},
		error: function () {
			window.location.href = 'login.html'
		}
	});
    });
}
//================================================================================================
function isIP(ip)
{
    var re =  /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/
    return re.test(ip);
}
