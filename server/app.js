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

app.post('/api/k', function(req, res){
    connection.query(`select * from company where code='${req.body.code}'`,(error, results, field)=>{
        if(error){
            res.json({error});
        }else{
            connection.query(`select * from kd_xueqiu where id=${results[0].id} order by date desc limit 1000`,(error, results, field)=>{  
                if(error){
                    res.json({error});
                }else{
                    res.json({results,field});
                }
            });        
        }
    });
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