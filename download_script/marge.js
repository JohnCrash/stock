var mysql   = require('mysql');
var Crawler = require("crawler");
var async = require("async");
var bigint = require("big-integer");

var connection = mysql.createPool({
    connectionLimit : 10,
    host     : 'localhost',
    user     : 'root',
    password : 'nv30ati2',
    database : 'stock'
  });

  function dateString(date){
    if(date)
        return `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`;
    else
        return 'null';
  }

/**
 * 将company sta_macd catorge表合并到company_detail
 */
  function mergeCompanyAndMacd(){
      let tasks = [];
      tasks.push((cb)=>{
        connection.query(`select * from company where category_base!=9`,(error, results, field)=>{
            if(error)
                console.error(error);
            cb(error,results);
        });
      });
      tasks.push((cb)=>{
        connection.query(`select * from category`,(error, results, field)=>{
            if(error)
                console.error(error);
            cb(error,results);            
        });
      });
      tasks.push((cb)=>{
        connection.query(`select * from category_base`,(error, results, field)=>{
            if(error)
                console.error(error);
            cb(error,results);            
        });
      });     
      tasks.push((cb)=>{
        connection.query(`select * from sta_macd`,(error, results, field)=>{
            if(error)
                console.error(error);
            cb(error,results);            
        });
      });
      async.parallel(tasks,(err,[company,category,category_base,macd])=>{
          if(err)return;
          let CategoryTable = {};
          let CategoryBaseTable = {};
          let MacdTable = {};
          for(let i in category){
            CategoryTable[category[i].id] = category[i].name;
          }
          for(let i in category_base){
            CategoryBaseTable[category[i].id] = category_base[i].name;
          }
          for(let i in macd){
            MacdTable[macd[i].company_id] = macd[i];
          }
          function getCategory(category,category_base){
              let c1 = CategoryTable[category];
              let c2 = CategoryBaseTable[category_base];
              if(c1 && c2){
                return `${c1}|${c2}`;
              }else if(c1){
                return c1;
              }else if(c2){
                return c2;
              }else return null;
          }
          function getMacd(id){
            return MacdTable[id]?MacdTable[id]:{income:null,positive_income:null,negative_income:null,static_income:null,opertor_num:null,positive_num:null,negative_num:null,usage_rate:null,hold_day:null};
          }
          
        let values = [];
        for(let i in company){
            let c = company[i];
            let category = getCategory(c.category,c.category_base);
            let kbegin = dateString(c.kbegin);
            let kend = dateString(c.kend);
            let {income,positive_income,negative_income,static_income,opertor_num,positive_num,negative_num,usage_rate,hold_day} = getMacd(c.id);
            let v = `${c.id},'${c.name}','${c.code}','${category}',0,'${kbegin}','${kend}',${income},${positive_income},${negative_income},${static_income},${opertor_num},${positive_num},${negative_num},${usage_rate},${hold_day}`;
            connection.query(`insert ignore into company_detail values (${v})`,(err,result,field)=>{
                if(err){
                    console.error(v);
                }
            });
        }

      });    
  }

  mergeCompanyAndMacd();