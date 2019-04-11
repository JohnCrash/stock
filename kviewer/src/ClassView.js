import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import {dateString,timestampString,getDayLength,days} from './kits';
import FetchChart from './FetchChart';
import GameChart from './GameChart';
import Button from '@material-ui/core/Button';
import Chip from '@material-ui/core/Chip';
import AttachMoneyIcon from '@material-ui/icons/AttachMoney';
import Typography from '@material-ui/core/Typography';
import macd from 'macd';

const upColor = '#ec0000';
const upBorderColor = '#ec0000';
const downColor = '#00da3c';
const downBorderColor = '#008F28';
const goldColor = '#ffd54f';
const buyColor = '#7c4dff';

const styles = theme => ({
    root: {
        width:'100%'     
    },
    graph:{
        width:'100%',
        display:'flex',

    },
    button: {
        margin: theme.spacing.unit
    },
    clip: {
        margin: theme.spacing.unit,
        primaryColor:{
            backgroundColor:'#00FF00',
            color:'#00FF00'
        }
    },
    control:{
        width:'100%',
        display:'flex',
        justifyContent:"center",
        flexWrap:"wrap"
    }   
  });

function p100(d){
    return Math.floor(d*10000)/10000;
}

function arrayScale(a,n){
    let s = [];
    for(let it of a){
        for(let i=0;i<n;i++)
            s.push(it);
    }
    return s;
}
const selects = {
    "保险业":1,
    "仓储业":1,
    "畜牧业":1,
    "电力、热力生产和供应业":1,
    "电气机械和器材制造业":1,
    "电信、广播电视和卫星传输服务":1,
    "房地产业":1,
    "废弃资源综合利用业":1,
    "非金属矿采选业":1,
    "非金属矿物制品业":1,
    "广播、电视、电影和影视录音制作业":1,
    "货币金融服务":1,
    "航空运输业":1,
    "互联网和相关服务":1,
    "化学纤维制造业":1,
    "化学原料和化学制品制造业":1,
    "计算机、通信和其他电子设备制造业":1,
    "酒、饮料和精制茶制造业":1,
    "教育":1,
    "木材加工和木、竹、藤、棕、草制品业":1,
    "煤炭开采和洗选业":1,
    "农副食品加工业":1,
    "农、林、牧、渔服务业":1,
    "农业":1,
    "批发业":1,
    "汽车制造业":1,
    "其他金融业":1,
    "软件和信息技术服务业":1,
    "燃气生产和供应业":1,
    "食品制造业":1,
    "生态保护和环境治理业":1,
    "铁路、船舶、航空航天和其他运输设备制造业":1,
    "石油和天然气开采业":1,
    "新闻和出版业":1,
    "通用设备制造业":1,
    "文化艺术业":1,
    "仪器仪表制造业":1,
    "医药制造业":1,
    "资本市场服务":1,
    "装卸搬运和运输代理业":1,
    "专用设备制造业":1,
    "专业技术服务业":1
};

class ClassView extends Component{
    constructor(props){
        super(props);
    }

    init = ([{results}])=>{
        let cats = results;
        let dates = [];
        let legends = [];
        let series = [];
        for(let c of cats){
            if(!(c.name in selects))continue;
            legends.push(c.name);
            let rate = [];
            let acc = [];
            for(let i=0;i<c.kds.length;i++){
                rate.push(c.kds[i].rate);
            }
            if(dates.length === 0){
                for(let i=0;i<c.kds.length;i++){
                    dates.push(dateString(c.kds[i].date));
                }
            }
            series.push({
                name:c.name,
                type:'line',
                symbol: 'none',
                data:rate
            });
        }
        
        let dl = Math.abs(Math.floor(12000/dates.length));
        return {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            axisPointer: {
                link: {xAxisIndex: 'all'}
            },            
            legend: {
                data: legends
            },             
            grid: [
                { //rate
                    left: '3%',
                    right: '3%',
                    height: '48%'
                },
                {//acc
                    left: '3%',
                    right: '3%',
                    top: '50%',
                    height: '48%'
                }              
            ],
            xAxis: [
                {
                    type: 'category',
                    data: dates,
                    scale: true,
                    boundaryGap : false,
                    axisLine: {onZero: false},
                    splitLine: {
                        interval:15,
                        show: true},
                    splitNumber: 16,
                    min: 'dataMin',
                    max: 'dataMax',
                    axisPointer: {
                        label:{
                            show:false
                        }
                    }
                },
                {
                    type: 'category',
                    gridIndex: 1,
                    data: dates,
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
                }],
            yAxis: [
                {
                    scale: true
                },
                {
                    scale: true,
                    gridIndex: 1,
                    splitNumber: 2,
                    axisLabel: {show: true},
                    axisLine: {show: true},
                    axisTick: {show: false},
                    splitLine: {show: false}
                }],
            dataZoom: [
                {
                    type: 'inside',
                    xAxisIndex: [0,1],
                    start: 100-dl,
                    end: 100
                }],
            series: series
        };
    }

    render(){
        let {classes} = this.props;
        return <div className={classes.root}>
            <FetchChart api={['/api/kd_category']} init={this.init} width="100%" height={860}/>
        </div>
    }
}

export default withStyles(styles)(ClassView);

