/**
 * 将全部子分类穿起来
 */
import React, { Component } from 'react';
import KQuery from './KQuery';
import MACDView from './MACDView';
import TrendingUp from '@material-ui/icons/TrendingUp';
import TrendingDown from '@material-ui/icons/TrendingDown';
import Typography from '@material-ui/core/Typography';

const Entry = [
    {
        title:'沪深数据',
        icon:<TrendingUp />,
        view:<KQuery/>
    },
    {
        title:'MACD',
        icon:<TrendingUp />,
        view:<MACDView />,
        default:true
    }
];

 export default Entry;