import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import MacdChart from './MacdChart';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import Paper from '@material-ui/core/Paper';
import KMacdChart from './KMacdChart';
import SwitchView from './SwitchView';

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
        title:'理论',
        desc:'严格在MACD为正时买入为负时卖出，买入和卖出使用当日平均价。',
        view:<Typography>
            严格在MACD为正时买入为负时卖出，买入和卖出使用当日平均价。
        </Typography>
    },
    {
        title:'交易表',
        desc:'查看个股在此理论的支持下的交易情况',
        view:<MacdChart width={'100%'} height={640} />
    },
    {
        title:'交易趋势表',
        desc:'将交易表放入在趋势图下',
        view:<KMacdChart width={'100%'} height={640} />
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

/*
            <Paper className={classes.paper}>
                <Typography>
                    严格在MACD为正时买入为负时卖出，买入和卖出使用当日平均价。
                </Typography>
            </Paper>
            <Paper className={classes.paper}>
                <TextField id="id-name" placeholder="股票名称或者代码" className={classes.textField} margin="normal" inputRef={(ref)=>this.inputRef=ref}/>
                <Button variant="contained" color="primary" className={classes.button} onClick={this.handleQuery.bind(this)}>查询</Button>
            </Paper>
            <MacdChart width={'100%'} height={640} code={this.state.code} />
            <KMacdChart width={'100%'} height={640} code={this.state.code} />
*/
export default withStyles(styles)(MacdStandardView);