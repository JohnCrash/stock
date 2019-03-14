let {companys_task,dateString,query,connection} = require('./k');
let {calc_tech_macd} = require('./macd');
let async = require('async');

calc_tech_macd(err=>{
    console.log('DONE!')
});