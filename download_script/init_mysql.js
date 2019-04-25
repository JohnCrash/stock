/**
 * 初始化mysql数据库
 */
const {query} = require('./k');
const async = require("async");

function addTask(task,str){
    task.push((cb)=>{
        query(str)
        .then(result=>{
            console.log('Create category table');
            cb();
        })
        .catch(err=>{
            console.error(err);
            cb(err);
        });    
    });
}

function initMySQL(){
    let task = [];

    //创建category表
    addTask(task,`CREATE TABLE \`stock\`.\`category\` (
        \`id\` INT NOT NULL AUTO_INCREMENT,
        \`name\` VARCHAR(16) NOT NULL,
        \`code\` VARCHAR(16) NOT NULL,
        \`simple\` VARCHAR(16) NOT NULL,
        \`url\` VARCHAR(128) NULL,
        PRIMARY KEY (\`id\`, \`code\`, \`name\`));`);    
    //创建company
    addTask(task,`CREATE TABLE \`stock\`.\`company\` (
        \`id\` INT NOT NULL AUTO_INCREMENT,
        \`code\` VARCHAR(16) NOT NULL,
        \`name\` VARCHAR(16) NOT NULL,
        \`category\` INT NULL,
        \`done\` INT NULL,
        \`kbegin\` DATE NULL,
        \`kend\` DATE NULL,
        \`amount\` FLOAT NULL,
        \`amplitude\` FLOAT NULL,
        \`chg\` FLOAT NULL,
        \`current\` FLOAT NULL,
        \`current_year_percent\` FLOAT NULL,
        \`dividend_yield\` FLOAT NULL,
        \`float_market_capital\` FLOAT NULL,
        \`hast_follow\` FLOAT NULL,
        \`lot_size\` FLOAT NULL,
        \`pb\` FLOAT NULL,
        \`pe_ttm\` FLOAT NULL,
        \`percent\` FLOAT NULL,
        \`percent5m\` FLOAT NULL,
        \`tick_size\` FLOAT NULL,
        \`type\` FLOAT NULL,
        \`volume\` FLOAT NULL,
        \`volume_ratio\` FLOAT NULL,
        \`ignore\` TINYINT NULL,
        PRIMARY KEY (\`id\`, \`code\`, \`name\`));
    `);
    //创建company_select
    addTask(task,`CREATE TABLE \`stock\`.\`company_select\` (
        \`company_id\` INT NOT NULL,
        \`code\` VARCHAR(16) NOT NULL,
        \`name\` VARCHAR(16) NOT NULL,
        \`category\` VARCHAR(16) NULL,
        \`ttm\` FLOAT NULL,
        \`pb\` FLOAT NULL,
        \`value\` FLOAT NULL,
        \`total\` FLOAT NULL,
        \`earnings\` FLOAT NULL,
        \`assets\` FLOAT NULL,
        \`dividend\` FLOAT NULL,
        \`yield\` FLOAT NULL,
        \`static30\` FLOAT NULL,
        \`static60\` FLOAT NULL,
        \`price\` FLOAT NULL,
        \`k15_max\` FLOAT NULL,
        \`k15_maxdrawal\` FLOAT NULL,
        \`k30_max\` FLOAT NULL,
        \`k30_maxdrawal\` FLOAT NULL,
        \`k60_max\` FLOAT NULL,
        \`k60_maxdrawal\` FLOAT NULL,
        \`bin4\` FLOAT NULL,
        \`glow\` FLOAT NULL,
        \`ma5diff\` FLOAT NULL,
        \`ma10diff\` FLOAT NULL,
        \`ma20diff\` FLOAT NULL,
        \`ma30diff\` FLOAT NULL,
        \`bookmark15\` FLOAT NULL,
        \`bookmark30\` FLOAT NULL,
        \`bookmark60\` FLOAT NULL,
        \`strategy1\` FLOAT NULL,
        \`strategy2\` FLOAT NULL,
        \`strategy3\` FLOAT NULL,
        PRIMARY KEY (\`company_id\`, \`code\`, \`name\`));
      `);
    //创建descript
    addTask(task,`CREATE TABLE \`stock\`.\`descript\` (
        \`company_id\` INT NOT NULL,
        \`name\` VARCHAR(16) NOT NULL,
        \`code\` VARCHAR(16) NOT NULL,
        \`desc\` TEXT NULL,
        \`site\` VARCHAR(128) NULL,
        \`phone\` VARCHAR(128) NULL,
        \`address\` VARCHAR(128) NULL,
        \`business\` VARCHAR(128) NULL,
        PRIMARY KEY (\`company_id\`, \`code\`, \`name\`));`); 
    //创建kd_xueqiu
    addTask(task,`CREATE TABLE \`stock\`.\`kd_xueqiu\` (
        \`id\` INT NOT NULL,
        \`date\` DATE NOT NULL,
        \`volume\` FLOAT NULL,
        \`open\` FLOAT NULL,
        \`high\` FLOAT NULL,
        \`low\` FLOAT NULL,
        \`close\` FLOAT NULL,
        \`chg\` FLOAT NULL,
        \`percent\` FLOAT NULL,
        \`turnoverrate\` FLOAT NULL,
        \`ma5\` FLOAT NULL,
        \`ma10\` FLOAT NULL,
        \`ma20\` FLOAT NULL,
        \`ma30\` FLOAT NULL,
        \`dea\` FLOAT NULL,
        \`dif\` FLOAT NULL,
        \`macd\` FLOAT NULL,
        PRIMARY KEY (\`id\`, \`date\`)) PARTITION BY HASH(id) PARTITIONS 64 ;`);    
    //创建k60_xueqiu
    addTask(task,`CREATE TABLE \`stock\`.\`k60_xueqiu\` (
        \`id\` INT NOT NULL,
        \`timestamp\` TIMESTAMP NOT NULL,
        \`volume\` FLOAT NULL,
        \`open\` FLOAT NULL,
        \`high\` FLOAT NULL,
        \`low\` FLOAT NULL,
        \`close\` FLOAT NULL,
        \`chg\` FLOAT NULL,
        \`percent\` FLOAT NULL,
        \`turnoverrate\` FLOAT NULL,
        \`dea\` FLOAT NULL,
        \`dif\` FLOAT NULL,
        \`macd\` FLOAT NULL,
        PRIMARY KEY (\`id\`, \`timestamp\`)) PARTITION BY HASH(id) PARTITIONS 128 ;`);
    //创建k15_xueqiu
    addTask(task,`CREATE TABLE \`stock\`.\`k15_xueqiu\` (
        \`id\` INT NOT NULL,
        \`timestamp\` TIMESTAMP NOT NULL,
        \`volume\` FLOAT NULL,
        \`open\` FLOAT NULL,
        \`high\` FLOAT NULL,
        \`low\` FLOAT NULL,
        \`close\` FLOAT NULL,
        \`chg\` FLOAT NULL,
        \`percent\` FLOAT NULL,
        \`turnoverrate\` FLOAT NULL,
        \`dea\` FLOAT NULL,
        \`dif\` FLOAT NULL,
        \`macd\` FLOAT NULL,
        PRIMARY KEY (\`id\`, \`timestamp\`)) PARTITION BY HASH(id) PARTITIONS 256 ;`);
    //创建k5_xueqiu
    addTask(task,`CREATE TABLE \`stock\`.\`k5_xueqiu\` (
        \`id\` INT NOT NULL,
        \`timestamp\` TIMESTAMP NOT NULL,
        \`volume\` FLOAT NULL,
        \`open\` FLOAT NULL,
        \`high\` FLOAT NULL,
        \`low\` FLOAT NULL,
        \`close\` FLOAT NULL,
        \`chg\` FLOAT NULL,
        \`percent\` FLOAT NULL,
        \`turnoverrate\` FLOAT NULL,
        \`dea\` FLOAT NULL,
        \`dif\` FLOAT NULL,
        \`macd\` FLOAT NULL,
        PRIMARY KEY (\`id\`, \`timestamp\`)) PARTITION BY HASH(id) PARTITIONS 512 ;`);
    //创建k5_segment
    addTask(task,`CREATE TABLE \`stock\`.\`k5_segment\` (
        \`id\` INT NOT NULL,
        \`timestamp\` TIMESTAMP NOT NULL,
        \`price\` FLOAT NULL,
        \`cycle\` int(11) DEFAULT NULL,
        \`pos\` int(11) DEFAULT NULL,        
        PRIMARY KEY (\`id\`, \`timestamp\`));`);
    //创建k15_segment
    addTask(task,`CREATE TABLE \`stock\`.\`k15_segment\` (
        \`id\` INT NOT NULL,
        \`timestamp\` TIMESTAMP NOT NULL,
        \`price\` FLOAT NULL,
        \`cycle\` int(11) DEFAULT NULL,
        \`pos\` int(11) DEFAULT NULL,        
        PRIMARY KEY (\`id\`, \`timestamp\`));`);
    //创建k60_segment
    addTask(task,`CREATE TABLE \`stock\`.\`k60_segment\` (
        \`id\` INT NOT NULL,
        \`timestamp\` TIMESTAMP NOT NULL,
        \`price\` FLOAT NULL,
        \`cycle\` int(11) DEFAULT NULL,
        \`pos\` int(11) DEFAULT NULL,        
        PRIMARY KEY (\`id\`, \`timestamp\`));`);
    //创建kd_segment
    addTask(task,`CREATE TABLE \`stock\`.\`kd_segment\` (
        \`id\` INT NOT NULL,
        \`date\` DATE NOT NULL,
        \`price\` FLOAT NULL,
        \`cycle\` int(11) DEFAULT NULL,
        \`pos\` int(11) DEFAULT NULL,        
        PRIMARY KEY (\`id\`, \`date\`));`);

    async.series(task,(err,results)=>{
        if(err)
            console.error(err);
        else
            console.log('DONE!');
    });
}

initMySQL();

