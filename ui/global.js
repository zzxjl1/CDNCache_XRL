//封装一下ajax get
function ajaxGet(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var data = JSON.parse(xhr.responseText);
            callback(data);
        }
    }
    xhr.send();
}

//解析url参数
function getUrlParam(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
    var r = window.location.search.substr(1).match(reg);
    if (r != null) return unescape(r[2]); return null;
}

function parse_name(url) {
    
    //?后面全部去掉
    url = url.split('?')[0];
    // '/get_cache_agent_reward' -> 'Cache Agent Reward'
    let temp = url.split('_');
    for (let i = 0; i < temp.length; i++) {
        // ['get', 'cache', 'agent', 'reward'] -> ['Get', 'Cache', 'Agent', 'Reward']
        temp[i] = temp[i].charAt(0).toUpperCase() + temp[i].slice(1);
    }
    // remove 'Get'
    temp.shift();
    var name = temp.join(' ');
    return name;
}