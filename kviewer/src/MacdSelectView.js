import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import SwitchView from './SwitchView';
import MacdChart from './MacdChart';
import MacdSelectChart from './MacdSelectChart';

const styles = theme => ({
});
const switchs=[
    {
        title:'今天可能变正',
        desc:'如果股票今天上涨很可能MACD将为正',
        view:<MacdSelectChart day={0} buy={1} width={'100%'} height={720} />
    },
    {
        title:'昨天收盘已经变正',
        desc:'昨天收盘的时候MACD已经变正',
        view:<MacdSelectChart  day={1} buy={1} width={'100%'} height={720} />
    },
    {
        title:'前天收盘已经变正',
        desc:'前天收盘的时候MACD已经变正',
        view:<MacdSelectChart  day={2} buy={1} width={'100%'} height={720} />
    },
    {
        title:'三天前收盘已经变正',
        desc:'三天前收盘的时候MACD已经变正',
        view:<MacdSelectChart  day={3} buy={1} width={'100%'} height={720} />
    }
];
class MacdSelectView extends Component{
    constructor(props){
        super(props);
    }

    render(){
        const { classes } = this.props;
        return <SwitchView switchs={switchs}/>
    }
}

export default withStyles(styles)(MacdSelectView);