const async = require('async');
const Crawler = require("crawler");

function list_page(n){
    uri = `http://summary.jrj.com.cn/scfl/msci.shtml?q=cn|s|msci&c=m&n=hqa&o=pl,d&p=${n}020`
    let c = new Crawler({
        maxConnections : 1,
        callback : function(error, res, done){
            var $ = res.$
            var li = $("tr")
            console.log(li)
            console.log(res.body)
        }
    });

    c.queue({
        uri:uri
    }); 
}

list_page(1)