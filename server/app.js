var express = require('express');
var serveStatic = require('serve-static');
var compression = require('compression');
var bodyParser = require('body-parser');
var cookieParser = require('cookie-parser');
var mysql   = require('mysql');

var connection = mysql.createPool({
    connectionLimit : 100,
    host     : 'localhost',
    user     : 'root',
    password : 'nv30ati2',
    database : 'stock'
  });

var app = express();

function dateString(date){
    return `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`;
}

function shouldCompress (req, res) {
    if (req.headers['x-no-compression']) {
      // don't compress responses with this request header
      return false;
    }
    // fallback to standard filter function
    return true;//compression.filter(req, res);
}
app.use(compression({filter: shouldCompress}));

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(serveStatic('public'));

function isStockCode(code){
    if(code && code.length===8){
      return code.match(/[sh|sz]\d{6}/i);
    }else{
      return false;
    }
}
/**
 * k线图查询
 */
app.post('/api/k', function(req, res){
    let queryStr;
    if(isStockCode(req.body.code)){
        queryStr = `code='${req.body.code}'`;
    }else{
        queryStr = `name='${req.body.code}'`;
    }
    connection.query(`select * from company where ${queryStr}`,(error, results, field)=>{
        if(error){
            res.json({error});
        }else if(results.length===1){
            let name  = results[0].name;
            let ry = req.body.range?req.body.range:1;
            connection.query(`select * from kd_xueqiu where id=${results[0].id} order by date desc limit ${ry*243}`,(error, results, field)=>{  
                if(error){
                    res.json({error:error.sqlMessage});
                }else{
                    res.json({results,field,name});
                }
            });        
        }else{
            res.json({error:`Not found '${req.body.code}'`});
        }
    });
});

/**
 * macd交易查询
 */
app.post('/api/macd', function(req, res){
    let queryStr;
    if(isStockCode(req.body.code)){
        queryStr = `code='${req.body.code}'`;
    }else{
        queryStr = `name='${req.body.code}'`;
    }
    connection.query(`select * from company where ${queryStr}`,(error, results, field)=>{
        if(error){
            res.json({error:error.sqlMessage});
        }else if(results.length===1){
            let name  = results[0].name;
            connection.query(`select * from tech_macd where company_id=${results[0].id} order by sell_date desc`,(error, results, field)=>{  
                if(error){
                    res.json({error:error.sqlMessage});
                }else{
                    res.json({results,field,name});
                }
            });        
        }else{
            res.json({error:`Not found '${req.body.code}'`});
        }
    });
});

/**
 * macd年收益分布
 */
app.post('/api/macd_distributed', function(req, res){
    let str1 = req.body.category?`category=${req.body.category}`:"";
    let str2 = req.body.year?`year=${req.body.year}`:"";
    let str = (str1 && str2)?`${str1} and ${str2}`:(str1+str2);
    connection.query(`select * from sta_macd_year where ${str}`,(error, results, field)=>{
        if(error){
            res.json({error:error.sqlMessage});
        }else if(results.length>0){
            let min = results[0].income;
            let max = results[results.length-1].income;
            let a = {};
            let positive = 0;
            let positiveNum = 0;
            let negative = 0;
            let negativeNum = 0;
            for(let v of results){
                let k = Math.floor(v.income/0.02);
                if(v.income>0){
                    positive+=v.income;
                    positiveNum++;
                }else{
                    negative+=v.income;
                    negativeNum++;
                }
                if(!a[k])a[k] = 0;
                a[k]++;
            }
            res.json({
                results:a,
                step:0.02,
                positive:positiveNum!=0?positive/positiveNum:0,
                negative:negativeNum!=0?negative/negativeNum:0,
                income:(positive+negative)/(positiveNum+negativeNum)
            });
        }else{
            res.json({error:`Not found '${req.body.code}'`});
        }
    });
});

/**
 * category返回股票分类表
 */
app.post('/api/category', function(req, res){
    connection.query(`select * from category`,(error, results, field)=>{
        if(error){
            res.json({error:error.sqlMessage});
        }else if(results.length>0){
            res.json({results});
        }else{
            res.json({error:`Not found`});
        }
    });
});

/**
 * macd买卖想信号
 */
app.post('/api/buysell', function(req, res){
    let ry = Number(req.body.range?req.body.range:1);
    let c = new Date(Date.now() - ry*365*24*3600*1000);
    connection.query(`select * from sta_macd_wave where date>'${dateString(c)}'`,(error, results, field)=>{
        if(error){
            res.json({error:error.sqlMessage});
        }else if(results.length>0){
            res.json({results});
        }else{
            res.json({error:`Not found`});
        }
    });
});

/**
 * 股票选择
 */
app.post('/api/select', function(req, res){
    let queryStr;
    let cmd = req.body.cmd;
    if(cmd &&cmd[0]==='#'){
        connection.query(`select * from company_detail where ${cmd.slice(1)}`,(error, results, field)=>{
            if(error){
                res.json({error:error.sqlMessage});
            }else if(results.length===0){
                res.json({error:`Not found '${cmd}'`});
            }else{
                res.json({results});
            }
        });
    }else{
        if(isStockCode(cmd)){
            queryStr = `code='${cmd}'`;
        }else{
            queryStr = `name='${cmd}'`;
        }
        connection.query(`select * from company_detail where ${queryStr}`,(error, results, field)=>{
            if(error){
                res.json({error:error.sqlMessage});
            }else if(results.length===0){
                res.json({error:`Not found '${cmd}'`});
            }else{
                res.json({results});
            }
        });
    }
});

// catch 404 and forward to error handler
app.use(function(req, res, next) {
    var err = new Error('Not Found');
    err.status = 404;
    next(err);
});

/* istanbul ignore next */
if (!module.parent) {
  app.listen(4000);
  console.log('Express started on port 4000');
}