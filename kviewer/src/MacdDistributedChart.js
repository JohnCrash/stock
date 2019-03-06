import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import FetchChart from './FetchChart';
import {postJson} from './fetch';
import Typography from '@material-ui/core/Typography';
import Button from '@material-ui/core/Button';
import {CompanyContext} from './CompanyContext';

const upColor = '#ec0000';
const upBorderColor = '#ec0000';
const downColor = '#00da3c';
const downBorderColor = '#008F28';

const styles = theme => ({
    root: {
        width:'100%'
      },
    button: {
    }
});

function buildYears(range){
    let a = new Date().getFullYear();
    let y = [];
    range = range?range:5;
    for(let i = a-range;i<=a;i++){
        y.push(String(i));
    }
    return y;
}

let category = null;

function precision(a,N){
    return Math.floor(a*N)/N;
}

class MacdDistributedChart extends Component{
    state = {
        current:String(new Date().getFullYear()),
        isall:true,
        currentCategory:null
    };
    componentDidMount(){
        if(!category)
            postJson('/api/category',{},(json)=>{
                if(json.error){
                    console.error(json.error);
                }else{
                    category = json.results;
                }
            });
    }
    handleChangeYear=(year)=>(event)=>{
        this.setState({current:year});
    };
    render(){
        const {classes} = this.props;
        const {current,isall,currentCategory} = this.state;
        const years = buildYears(this.context.range);
        let _this = this;
        return (<div className={classes.root}>
        {years.map((item)=>{
            return <Button  variant="contained" key={item} color={item===current?"secondary":"primary"} className={classes.button} onClick={_this.handleChangeYear(item)}>
                {item}
            </Button>
        })}
        <FetchChart api='/api/macd_distributed' args={{year:current,category:currentCategory}} init={
            ({step,results,positive,negative,income})=>{
                let dates = [];
                let values = [];
                let rows = [];
                positive = precision(positive,1000);
                negative = precision(negative,1000);
                for(let i in results){
                    let n = results[i];
                    rows.push({value:i,number:n});
                }
                rows.sort((a,b)=>{
                    return a.value - b.value;
                });
                let k=0;
                for(let v of rows){
                    dates.push(precision(v.value*step,100));
                    values.push([k,v.number,v.value]);
                    k++;
                }
                return {
                    grid: [{
                            left: '6%',
                            right: '3%',
                            height: '70%'
                        },
                        {
                            left: '6%',
                            right: '3%',
                            top: '83%',
                            height: '6%'
                        }
                    ],
                    visualMap: [{
                        show: false,
                        seriesIndex: 0,
                        dimension: 2,
                        pieces: [{
                            max: 0,
                            color: downColor
                        }, {
                            min: 0,
                            color: upColor
                        }]
                    },
                    {
                        show: false,
                        seriesIndex: [1,2,3],
                        dimension: 0,
                        pieces: [{
                            max: 0,
                            color: downColor
                        }, {
                            min: 0,
                            color: upColor
                        }]
                    }],
                    tooltip: {},
                    xAxis: [
                        {
                        data: dates,
                        silent: false,
                        splitLine: {
                            show: false
                            }
                        },
                        {
                            type : 'value',
                            gridIndex: 1,
                        }                        
                    ],
                    yAxis: [
                        {
                        },
                        {
                            type : 'category',
                            gridIndex: 1,
                            axisTick : {show: false},
                            data : ['统计']
                        }
                    ],
                    series: [{
                        name: current,
                        type: 'bar',
                        data: values
                    },
                    {
                        name:'利润',
                        type:'bar',
                        xAxisIndex: 1,
                        yAxisIndex: 1,                        
                        label: {
                            normal: {
                                show: true,
                                position: 'inside'
                            }
                        },
                        data:[precision(income,1000)]
                    },                
                    {
                        name:'收入',
                        type:'bar',
                        xAxisIndex: 1,
                        yAxisIndex: 1,                        
                        stack: '总量',
                        label: {
                            normal: {
                                show: true
                            }
                        },
                        itemStyle:{
                            color:upColor
                        },
                        data:[positive]
                    },
                    {
                        name:'支出',
                        type:'bar',
                        xAxisIndex: 1,
                        yAxisIndex: 1,
                        stack: '总量',
                        label: {
                            normal: {
                                show: true,
                                position: 'left'
                            }
                        },
                        itemStyle:{
                            color:downColor
                        },
                        data:[negative]
                    }
                ]
                };            
            }
        } {...this.props}/>
        <Button variant="contained" color={isall?"secondary":"primary"} key={"main"} onClick={()=>this.setState({isall:true,currentCategory:null})}>
            全部
        </Button>
        {isall?<Button variant="contained" color={isall?"primary":"secondary"} key={"category"} onClick={()=>this.setState({isall:false})}>
            分类
        </Button>:category?category.map((item)=>{
            return <Button variant="contained" color={currentCategory===item.id?"secondary":"primary"} key={item.id} onClick={()=>this.setState({currentCategory:item.id})}>
                {item.name}
            </Button>
        }):undefined}
        </div>);
    }
}

MacdDistributedChart.contextType = CompanyContext;
export default withStyles(styles)(MacdDistributedChart);