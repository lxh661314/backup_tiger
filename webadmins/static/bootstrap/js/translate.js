/**
 * Created by reonard on 16/12/29.
 */


var message_cn = [];

message_cn['DockerTask'] = '容器应用';
message_cn['TraditionTask'] = '非容器应用';
message_cn['unbind'] = '未绑定容器应用';

function get_cn(message){
    if (message_cn[message] != undefined)
        return message_cn[message];
    else
        return message
}