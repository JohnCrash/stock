import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import MacdChart from './MacdChart';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import Paper from '@material-ui/core/Paper';
import KMacdChart from './KMacdChart';
import SwitchView from './SwitchView';
import MacdYearRateChart from './MacdYearRateChart';
import MacdDistributedChart from './MacdDistributedChart';
import MacdBuyShellChart from './MacdBuyShellChart';

const styles = theme => ({
    button: {
        margin: theme.spacing.unit,
    },    
    textField: {
        marginLeft: theme.spacing.unit,
        marginRight: theme.spacing.unit,
        width: 200,
      },      
    paper:{
        margin:3*theme.spacing.unit
    },
    heading: {
      fontSize: theme.typography.pxToRem(15),
      flexBasis: '33.33%',
      flexShrink: 0,
    },
    secondaryHeading: {
      fontSize: theme.typography.pxToRem(15),
      color: theme.palette.text.secondary,
    },
});

const switchs=[
    {
        title:'交易表',
        desc:'查看个股在此理论的支持下的交易情况',
        view:<MacdChart width={'100%'} height={640} />
    },
    {
        title:'交易趋势表',
        desc:'将交易表放入在趋势图下，图表从上到下依次是K线、成交量、MACD、交易盈亏、金叉死叉分布',
        view:<KMacdChart width={'100%'} height={820} />
    },
    {
        title:'年收益率',
        desc:'将指定年的收益率叠加',
        view:<MacdYearRateChart width={'100%'} height={640} /> 
    },
    {
        title:'收益率分布',
        desc:'看看每种收益率下有多少只股票',
        view:<MacdDistributedChart width={'100%'} height={640} /> 
    },
    {
        title:'信号分布',
        desc:'将每天进入macd买入点和卖出点的股票数量作为y，日期作为x',
        view:<MacdBuyShellChart width={'100%'} height={640} /> 
    },
    {
        title:'股价、市值、市盈率收益分布',
        desc:'将股价、市值、市盈率作为横坐标，将收益率作为纵坐标',
        view:<MacdDistributedChart width={'100%'} height={640} /> 
    },    
    {
        title:'周期分布',
        desc:'将macd的周期天数作为y，日期作为x',
        view:<MacdDistributedChart width={'100%'} height={640} /> 
    },
    {
        title:'理论与分析',
        desc:'严格在MACD为正时买入为负时卖出，买入和卖出使用当日平均价。',
        view:<Typography>
            严格在MACD为正时买入为负时卖出，买入和卖出使用当日平均价。
        </Typography>
    }    
];

class MacdStandardView extends Component{
    constructor(props){
        super(props);
    }
    render(){
        const { classes } = this.props;
        return <SwitchView switchs={switchs}/>
    }
}

export default withStyles(styles)(MacdStandardView);