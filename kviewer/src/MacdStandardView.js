import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import MacdChart from './MacdChart';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import Paper from '@material-ui/core/Paper';
import KMacdChart from './KMacdChart';
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
    }
});

class MacdStandardView extends Component{
    constructor(props){
        super(props);
        this.state = {code:'SH000001'};
    }
    handleQuery = (event)=>{
        this.setState({code:this.inputRef.value});
    }
    render(){
        const { classes } = this.props;
        return <div>
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
        </div>
    }
}

export default withStyles(styles)(MacdStandardView);