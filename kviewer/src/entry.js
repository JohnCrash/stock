/**
 * 将全部子分类穿起来
 */
import React, { Component } from 'react';
import KQuery from './KQuery';
import MACDView from './MACDView';
import TrendingUp from '@material-ui/icons/TrendingUp';
import TrendingDown from '@material-ui/icons/TrendingDown';
import Typography from '@material-ui/core/Typography';
import GameView from './GameView';
import K15View from './K15View';
import ClassView from './ClassView';
import StockSelectView from './StockSelectView';

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
    },
    {
        title:'K15',
        icon:<TrendingUp />,
        view:<K15View />
    },  
    {
        title:'练习',
        icon:<TrendingUp />,
        view:<GameView />,
    },
    {
        title:'选股',
        icon:<TrendingUp />,
        view:<StockSelectView />,
    }
];

 export default Entry;