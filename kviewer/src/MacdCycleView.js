import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';

const styles = theme => ({
});

class MacdCycleView extends Component{
    constructor(props){
        super(props);
    }

    render(){
        const { classes } = this.props;
        return <Typography>
            根据MACD的涨落周期进行提前卖出。
        </Typography>
    }
}

export default withStyles(styles)(MacdCycleView);