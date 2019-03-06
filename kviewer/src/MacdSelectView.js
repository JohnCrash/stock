import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import SwitchView from './SwitchView';
import MacdChart from './MacdChart';

const styles = theme => ({
});
const switchs=[
    {
        title:'MACD',
        desc:'MACD搞好要变成正的股票列表',
        view:<MacdChart width={'100%'} height={640} />
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