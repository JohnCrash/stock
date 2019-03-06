import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';

const styles = theme => ({
});

class MacdSelectView extends Component{
    constructor(props){
        super(props);
    }

    render(){
        const { classes } = this.props;
        return <Typography>
            综合考虑使用周期和大盘优化。
        </Typography>
    }
}

export default withStyles(styles)(MacdSelectView);