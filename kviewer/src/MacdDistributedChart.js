import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import FetchChart from './FetchChart';
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

class MacdDistributedChart extends Component{
    state = {
        current:String(new Date().getFullYear())
    };
    
    handleChangeYear=(year)=>(event)=>{
        this.setState({current:year});
    };
    render(){
        const {classes} = this.props;
        const {current} = this.state;
        const years = buildYears(this.context.range);
        let _this = this;
        return (<div className={classes.root}>
        {years.map((item)=>{
            return <Button  variant="contained" color={item===current?"secondary":"primary"} className={classes.button} onClick={_this.handleChangeYear(item)}>
                {item}
            </Button>
        })}
        <FetchChart api='/api/macd_distributed' args={{year:current}} init={
            ({step,results})=>{
                let dates = [];
                let values = [];
                let rows = [];
                for(let i in results){
                    let n = results[i];
                    rows.push({value:i,number:n});
                }
                rows.sort((a,b)=>{
                    return a.value - b.value;
                });
                let k=0;
                for(let v of rows){
                    dates.push(v.value*step);
                    values.push([k,v.number,v.value]);
                    k++;
                }
                return {

                    visualMap: {
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
                    tooltip: {},
                    xAxis: {
                        data: dates,
                        silent: false,
                        splitLine: {
                            show: false
                        }
                    },
                    yAxis: {
                    },
                    series: [{
                        name: current,
                        type: 'bar',
                        data: values
                    }]
                };            
            }
        } {...this.props}/>
        <Typography>
            每条线代表年收益率
        </Typography>
        </div>);
    }
}

MacdDistributedChart.contextType = CompanyContext;
export default withStyles(styles)(MacdDistributedChart);