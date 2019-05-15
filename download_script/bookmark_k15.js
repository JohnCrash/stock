const {research_k15} = require('./research_k15');
const {update_company,update_desc} = require('./desc');

research_k15((err)=>{
    console.log('DONE!');
});

//update_desc(err=>{
//    console.log('done!')
//});