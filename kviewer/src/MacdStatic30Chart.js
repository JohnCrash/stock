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
        width:'100%',
        display:'flex',
        justifyContent:"center",
        flexWrap:"wrap"
      },
    button: {
    }
});

const W = 620;
class MacdStatic30Chart extends Component{
    state = {
    };
    componentDidMount(){
    }
    render(){
        const {classes} = this.props;

        return <div className={classes.root}><FetchChart api='/api/static30' init={
            ({results})=>{
                let data = [];
                for(let it of results){
                    if(it.price&&it.ttm&&it.static30&&it.price<100&&it.ttm<100){
                        data.push([it.price,it.ttm,it.static30]);
                    }
                }
                return {
                    tooltip: {},
                    backgroundColor: '#fff',
                    visualMap: [{
                        type: 'continuous',
                        min: -0.5,
                        max: 1,
                        precision: 1,
                        dimension: 2,
                        calculable : true,
                        color: [upColor,downColor]
                    }],
                    xAxis3D: {
                        type: 'value',
                        name:'价格'
                    },
                    yAxis3D: {
                        type: 'value',
                        name:'市盈率'
                    },
                    zAxis3D: {
                        type: 'value',
                        name:'30天涨幅'
                    },
                    grid3D: {
                        viewControl: {
                            // projection: 'orthographic'
                        }
                    },
                    series: [{
                        type: 'scatter3D',
                        data:data
                    }]
                }
            }
        } width={W} height={W}/>
        <FetchChart api='/api/static30' init={
            ({results})=>{
                let data = [];
                for(let it of results){
                    if(it.price&&it.ttm&&it.static30&&it.price<100&&it.ttm<100){
                        let value = it.value/100000000;
                        if(value<4000 &&value>0){
                            data.push([it.price,value,it.static30]);
                        }
                    }
                }
                return {
                    tooltip: {},
                    backgroundColor: '#fff',
                    visualMap: [{
                        type: 'continuous',
                        min: -0.5,
                        max: 1,
                        precision: 1,
                        dimension: 2,
                        calculable : true,
                        color: [upColor,downColor]
                    }],
                    xAxis3D: {
                        type: 'value',
                        name:'价格'
                    },
                    yAxis3D: {
                        type: 'value',
                        name:'市值'
                    },
                    zAxis3D: {
                        type: 'value',
                        name:'30天涨幅'
                    },
                    grid3D: {
                        viewControl: {
                            // projection: 'orthographic'
                        }
                    },
                    series: [{
                        type: 'scatter3D',
                        data:data
                    }]
                }
            }
        } width={W} height={W}/>
        <FetchChart api='/api/static30' init={
            ({results})=>{
                let data = [];
                for(let it of results){
                    if(it.price&&it.ttm&&it.static30&&it.price<100&&it.ttm<100&&it.pb<50){
                        data.push([it.ttm,it.pb,it.static30]);
                    }
                }
                return {
                    tooltip: {},
                    backgroundColor: '#fff',
                    visualMap: [{
                        type: 'continuous',
                        min: -0.5,
                        max: 1,
                        precision: 1,
                        dimension: 2,
                        calculable : true,
                        color: [upColor,downColor]
                    }],
                    xAxis3D: {
                        type: 'value',
                        name:'市盈率'
                    },
                    yAxis3D: {
                        type: 'value',
                        name:'市净率'
                    },
                    zAxis3D: {
                        type: 'value',
                        name:'30天涨幅'
                    },
                    grid3D: {
                        viewControl: {
                            // projection: 'orthographic'
                        }
                    },
                    series: [{
                        type: 'scatter3D',
                        data:data
                    }]
                }
            }
        } width={W} height={W}/>
        <FetchChart api='/api/static30' init={
            ({results})=>{
                let data = [];
                for(let it of results){
                    if(it.price&&it.ttm&&it.static30&&it.price<100&&it.ttm<100&&it.pb<50){
                        data.push([it.earnings,it.assets,it.static30]);
                    }
                }
                return {
                    tooltip: {},
                    backgroundColor: '#fff',
                    visualMap: [{
                        type: 'continuous',
                        min: -0.5,
                        max: 1,
                        precision: 1,
                        dimension: 2,
                        calculable : true,
                        color: [upColor,downColor]
                    }],
                    xAxis3D: {
                        type: 'value',
                        name:'每股收益'
                    },
                    yAxis3D: {
                        type: 'value',
                        name:'每股净资产'
                    },
                    zAxis3D: {
                        type: 'value',
                        name:'30天涨幅'
                    },
                    grid3D: {
                        viewControl: {
                            // projection: 'orthographic'
                        }
                    },
                    series: [{
                        type: 'scatter3D',
                        data:data
                    }]
                }
            }
        } width={W} height={W}/></div>
    }
}

MacdStatic30Chart.contextType = CompanyContext;
export default withStyles(styles)(MacdStatic30Chart);