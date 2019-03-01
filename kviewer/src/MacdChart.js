import React, { Component } from 'react';
import FetchChart from './FetchChart';

const upColor = '#ec0000';
const upBorderColor = '#ec0000';
const downColor = '#00da3c';
const downBorderColor = '#008F28';

function MacdChart(props){
    let {} = props;
    return <FetchChart api='/api/macd' args={{code:props.code}} init={
        ({name,results})=>{
            let dates = [];
            let values = [];
            results.reverse().forEach(e => {
                let d = new Date(e.sell_date);
                let dateString = `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()}`;
                dates.push(dateString);
                values.push(e.rate);
            });        
            return {
            //    title: {
            //        text: name
            //    },
                legend: {
                    data: [name],
                    align: 'left'
                },
                visualMap: {
                    show: false,
                    seriesIndex: 0,
                    dimension: 1,
                    pieces: [{
                        max: 0,
                        color: downColor
                    }, {
                        min: 0,
                        color: upColor
                    }]
                },            
                toolbox: {
                    // y: 'bottom',
                    feature: {
                        magicType: {
                            type: ['stack', 'tiled']
                        },
                        dataView: {},
                        saveAsImage: {
                            pixelRatio: 2
                        }
                    }
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
                    name: name,
                    type: 'bar',
                    data: values
                }]
            };            
        }
    } {...props}/>;
}

export default MacdChart;