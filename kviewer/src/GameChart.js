import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import {dateString,getDayLength,days} from './kits';
import FetchChart from './FetchChart';

const upColor = '#ec0000';
const upBorderColor = '#ec0000';
const downColor = '#00da3c';
const downBorderColor = '#008F28';
const goldColor = '#ffd54f';
const buyColor = '#7c4dff';

const styles = theme => ({
    root: {
        width:'100%'
      }
});


class GameChart extends Component{  
    constructor(props){
        super(props);
        this.state={}
    }
    componentDidMount(){
        let {thisCallBack} = this.props;
        thisCallBack(this);
    }
    cur(){
        if(this.i && this.dates && this.i<this.dates.length){
            return {
                date : this.dates[this.i],
                value : this.values[this.i]
            }
        }
    }
    next(buypt){
        if(this.i && this.options && this.echart && this.dates.length>this.i+1){
            this.i++;
            let i = this.i;
            /**
             * 更新图表
             */
            let options = this.options;
            let date = this.dates[i];
            let k = this.values[i];
            let ma5 = this.ma5[i];
            let ma10 = this.ma10[i];
            let ma20 = this.ma20[i];
            let ma30 = this.ma30[i];
            let volume = this.volume[i];
            let macd = this.macd[i];
            let buy = this.buys[i];
            let sell = this.sells[i];
            let positive = this.positives[i];
            let negative = this.negatives[i];

            options.xAxis[0].data.push(date);

            options.series[0].data.push(k);
            options.series[1].data.push(ma5);
            options.series[2].data.push(ma10);
            options.series[3].data.push(ma20);
            options.series[4].data.push(ma30);
            options.series[5].data.push(volume);
            options.series[6].data.push(macd);
            options.series[7].data.push(buy);
            options.series[8].data.push(sell);
            options.series[9].data.push(positive);
            options.series[10].data.push(negative);

            let dates = options.xAxis[0].data;
            let dd = getDayLength(dates[0],dates[dates.length-1]);
            let dl = 100-Math.abs(Math.floor(6000/dd));
            options.dataZoom[0].start = dl;
            options.dataZoom[0].end = 100;

            //将增长显示出来
            if(buypt){
                options.series[0].markArea.itemStyle = {color:buypt>k[1]?'#00FF00':'#FF0000',opacity:0.2}
                options.series[0].markArea.data = [[{yAxis:buypt},{yAxis:k[1]}]];
            }
            else
                options.series[0].markArea.data = [];
            this.echart.setOption(this.options);
            return this.cur();
        }
    }
    init = (a)=>{
        let name = a[0].name;
        let results = a[0].results;
        let dates = [];
        let values = [];
        let ma5 = [];
        let ma10 = [];
        let ma20 = [];
        let ma30 = [];
        let volume = [];
        let macd = [];
        let merchsData = a[1].results;
        let merchs = [];
        let {rand} = this.props;

        this.dates = dates;
        this.values = values;
        this.ma5 = ma5;
        this.ma10 = ma10;
        this.ma20 = ma20;
        this.ma30 = ma30;
        this.volume = volume;
        this.macd = macd;
        
        console.log(rand);
        // 将macd交易数据的时间整合到k的时间线上
        let merchsMaps = {};
        for(let v of merchsData){
            //merchsMaps[v.buy_date] = v;
            //merchsMaps[v.sell_date] = v;
            //将中间填满
            for(let d of days(v.buy_date,v.sell_date)){
                merchsMaps[d] = v;
            }
        }

        function getMerchsRate(date,i){
            let v = merchsMaps[date];
            return [i,v?v.rate:0,date&&v&&v.max_date&&date==v.max_date?-1:1];
        }
        results.reverse().forEach((element,i) => {
            let dateStr = dateString(element.date);
            dates.push(dateStr);
            values.push([element.open,element.close,element.low,element.high]);
            ma5.push(element.ma5);
            ma10.push(element.ma10);
            ma20.push(element.ma20);
            ma30.push(element.ma30);
            //volume.push([i,element.volume,element.close-element.open]);
            volume.push(element.volume);
            macd.push(element.macd);
            merchs.push(getMerchsRate(element.date,i)); //将改天的交易数据放入，没有就是0
        });
        //金叉死叉分布，将时间走同步的kd线一致
        //=================================
        let buysells = a[2].results;
        let dateBuySell = {};
        let buys = [];
        let sells = [];
        let positives = [];
        let negatives = [];
        
        this.buys = buys;
        this.sells = sells;
        this.positives = positives;
        this.negatives = negatives;

        for(let i=0;i<buysells.length;i++){
            let v = buysells[i];
            dateBuySell[dateString(v.date)] = {buy:v.buy,sell:v.sell,positive:v.positive,negative:v.negative};
        }
        for(let d of dates){
            let v = dateBuySell[dateString(d)];
            if(v){
                buys.push(v.buy);
                sells.push(-v.sell);
                positives.push(v.positive);
                negatives.push(-v.negative);       
            }else{
                buys.push(0);
                sells.push(0);
                positives.push(0);
                negatives.push(0);                   
            }
        }
        //=================================
        /**
         * 重新设置区域
         */
        let dates_ = [];
        let values_ = [];
        let ma5_ = [];
        let ma10_ = [];
        let ma20_ = [];
        let ma30_ = [];
        let volume_ = [];
        let macd_ = [];
        let merchs_ = [];
        let buys_ = [];
        let sells_ = [];
        let positives_ = [];
        let negatives_ = [];
        let start = Math.floor(dates.length*rand);
        if(start<30)
            start = 30;
        this.start = start;
        this.dates_ = dates_;
        this.values_ = values_;
        this.ma5_ = ma5_;
        this.ma10_ = ma10_;
        this.ma20_ = ma20_;
        this.ma30_ = ma30_;
        this.volume_ = volume_;
        this.macd_ = macd_;
        this.buys_ = buys_;
        this.sells_ = sells_;
        this.positives_ = positives_;
        this.negatives_ = negatives_;

        this.i = start-1;

        for(let i=0;i<30;i++){
            let k = start+i-30;
            dates_.push(dates[k]);
            values_.push(values[k]);
            ma5_.push(ma5[k]);
            ma10_.push(ma10[k]);
            ma20_.push(ma20[k]);
            ma30_.push(ma30[k]);
            volume_.push(volume[k]);
            macd_.push(macd[k]);
            merchs_.push(merchs[k]);

            buys_.push(buys[k]);
            sells_.push(sells[k]);
            positives_.push(positives[k]);
            negatives_.push(negatives[k]);            
        }

        let dl = Math.abs(Math.floor(6000/getDayLength(dates_[0],dates_[dates_.length-1])));
        this.dl = dl;
        let markarea = [[{yAxis:0},{yAxis:0}]];
        this.options = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            legend: {
                data: ['日K', 'MA5', 'MA10', 'MA20', 'MA30','成交量','MACD','金叉','死叉','macd正','macd负']
            },
            visualMap: [
                {
                    show: false,
                    seriesIndex: [6],
                    dimension: 1,
                    pieces: [{
                        max: 0,
                        color: downColor
                    }, {
                        min: 0,
                        color: upColor
                    }]
                }
            ],
            tooltip: {
                trigger: 'axis',
                triggerOn:'click',
                axisPointer: {
                    type: 'cross'
                },
                backgroundColor: 'rgba(245, 245, 245, 0.5)',
                borderWidth: 1,
                borderColor: '#ccc',
                padding: 10,
                textStyle: {
                    color: '#000'
                },
                formatter:(params)=>{
                    return ``;
                }
            },    
            axisPointer: {
                link: {xAxisIndex: 'all'}
            },
            grid: [
                { //k
                    left: '5%',
                    right: '5%',
                    height: '48%'
                },
                {//volume
                    left: '5%',
                    right: '5%',
                    top: '58%',
                    height: '12%'
                },
                {//macd
                    left: '5%',
                    right: '5%',
                    top: '73%',
                    height: '12%'
                },
                {//sign
                    left: '5%',
                    right: '5%',
                    top: '84%',
                    height: '16%'
                }        
            ],
            xAxis: [
                { //k
                    type: 'category',
                    data: dates_,
                    scale: true,
                    boundaryGap : false,
                    axisLine: {onZero: false},
                    splitLine: {show: false},
                    splitNumber: 20,
                    min: 'dataMin',
                    max: 'dataMax',
                    axisPointer: {
                        label:{
                            show:false
                        }
                    },
                    axisLabel:{show:false}
                },
                { //volume
                    type: 'category',
                    gridIndex: 1,
                    data: dates_,
                    scale: true,
                    boundaryGap : false,
                    axisLine: {onZero: true},
                    axisTick: {show: false},
                    splitLine: {show: false},
                    axisLabel: {show: false},
                    splitNumber: 20,
                    min: 'dataMin',
                    max: 'dataMax',
                    axisPointer: {
                        label:{
                            show:false
                        }
                    }
                },
                { //macd
                    type: 'category',
                    gridIndex: 2,
                    data: dates_,
                    scale: false,
                    boundaryGap : false,
                    axisLine: {onZero: true},
                    axisTick: {show: false},
                    splitLine: {show: false},
                    axisLabel: {show: false},
                    splitNumber: 20,
                    min: 'dataMin',
                    max: 'dataMax',
                    axisPointer: {
                        label:{
                            show:false
                        }
                    }
                },                
                { //sign
                    type: 'category',
                    gridIndex: 3,
                    data: dates_,
                    scale: true,
                    boundaryGap : false,
                    axisLine: {onZero: true},
                    axisTick: {show: false},
                    splitLine: {show: false},
                    axisLabel: {show: false},
                    splitNumber: 20,
                    min: 'dataMin',
                    max: 'dataMax',
                    axisPointer: {
                        label:{
                            show:false
                        }
                    }
                }
            ],
            yAxis: [
                { //k
                    scale: true,
                    splitArea: {
                        show: true
                    }
                },
                { //volume
                    scale: true,
                    gridIndex: 1,
                    splitNumber: 2,
                    axisLabel: {show: true},
                    axisLine: {show: true},
                    axisTick: {show: false},
                    splitLine: {show: false}
                },
                { //macd
                    scale: true,
                    gridIndex: 2,
                    splitNumber: 2,
                    axisLabel: {show: true},
                    axisLine: {show: true},
                    axisTick: {show: false},
                    splitLine: {show: false}
                },
                { //sign
                    scale: true,
                    gridIndex: 3,
                    splitNumber: 2,
                    axisLabel: {show: true},
                    axisLine: {show: true},
                    axisTick: {show: false},
                    splitLine: {show: false}
                }                         
            ],
            dataZoom: [
                {
                    type: 'inside',
                    xAxisIndex: [0,1,2,3],
                    start: 100-dl,
                    end: 100,
                    zoomLock:true
                }           
            ],
            series: [
                {
                    name: '日K',
                    type: 'candlestick',
                    data: values_,
                    itemStyle: {
                        normal: {
                            color: upColor,
                            color0: downColor,
                            borderColor: upBorderColor,
                            borderColor0: downBorderColor
                        }
                    },
                    markArea:{
                        data: markarea
                    }
                },
                {
                    name: 'MA5',
                    type: 'line',
                    symbol: 'none',
                    data: ma5_,
                    smooth: true,
                    itemStyle: {
                        normal: {color:'#fdd835'}
                    }
                },
                {
                    name: 'MA10',
                    type: 'line',
                    symbol: 'none',
                    data: ma10_,
                    smooth: true,
                    itemStyle: {
                        normal: {color:'#0277bd'}
                    }
                },
                {
                    name: 'MA20',
                    type: 'line',
                    symbol: 'none',
                    data: ma20_,
                    smooth: true,
                    itemStyle: {
                        normal: {color:'#ab47bc'}
                    }
                },
                {
                    name: 'MA30',
                    type: 'line',
                    symbol: 'none',
                    data: ma30_,
                    smooth: true,
                    itemStyle: {
                        normal: {color:'#ef6c00'}
                    }
                },
                {
                    name: '成交量',
                    type: 'bar',
                    xAxisIndex: 1,
                    yAxisIndex: 1,
                    data: volume_
                },                
                {
                    name: 'MACD',
                    type: 'bar',
                    xAxisIndex: 2,
                    yAxisIndex: 2,
                    data: macd_
                },               
                {
                    name: '金叉',
                    type: 'bar',
                    stack:'one',
                    data: buys_,
                    xAxisIndex: 3,
                    yAxisIndex: 3,                    
                    itemStyle:{
                        color : upColor
                    }
                },
                {
                    name: '死叉',
                    type: 'bar',
                    stack:'one',
                    data : sells_,
                    xAxisIndex: 3,
                    yAxisIndex: 3,                    
                    itemStyle:{
                        color : downColor
                    }
                },
                {
                    name: 'macd正',
                    type: 'line',
                    stack:'two',
                    data: positives_,
                    xAxisIndex: 3,
                    yAxisIndex: 3,                    
                    itemStyle:{
                        color : upColor
                    }
                },
                {
                    name: 'macd负',
                    type: 'line',
                    stack:'two',
                    data : negatives_,
                    xAxisIndex: 3,
                    yAxisIndex: 3,                    
                    itemStyle:{
                        color : downColor
                    }
                }
            ]            
        };
        return this.options;      
    };
    refChartCallback(echart){
        this.echart = echart;
    }
    render(){
        let {classes,step} = this.props;
    
        return <div className={classes.root}>
            <FetchChart api={['/api/k','/api/macd','/api/buysell']} refChartCallback={this.refChartCallback.bind(this)} init={this.init} {...this.props}/>
        </div>;
    }
}


export default withStyles(styles)(GameChart);