let {companys_task,dateString,query,connection} = require('./k');
let {calc_tech_macd,calc_macd_wave} = require('./macd');
let async = require('async');

calc_macd_wave(err=>{
    console.log('DONE!')
});