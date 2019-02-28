import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';

const styles = theme => ({
});

class MacdWideView extends Component{
    constructor(props){
        super(props);
    }

    render(){
        const { classes } = this.props;
        return <Typography>
            将大盘的情况考虑进去
        </Typography>
    }
}

export default withStyles(styles)(MacdWideView);