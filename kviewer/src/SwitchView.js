import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';

import ExpansionPanel from '@material-ui/core/ExpansionPanel';
import ExpansionPanelDetails from '@material-ui/core/ExpansionPanelDetails';
import ExpansionPanelSummary from '@material-ui/core/ExpansionPanelSummary';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import Typography from '@material-ui/core/Typography';

const styles = theme => ({
    root:{},
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

/**
 * 切换不同的view
 * case属性的结构title,desc,view
 */
class SwitchView extends Component{
    constructor(props){
        super(props);
        this.state = {expanded:false};
    }
    handleChange=panel=>(event,expanded)=>{
        this.setState({expanded: expanded ? panel : false,});
    }    
    render(){
        const { classes,switchs } = this.props;
        const { expanded } = this.state;
        return <div className={classes.root}>
            {switchs.map((item,index)=>{
                return <ExpansionPanel expanded={expanded === item.title} key={item.title} onChange={this.handleChange(item.title)}>
                    <ExpansionPanelSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography className={classes.heading}>{item.title}</Typography>
                        <Typography className={classes.secondaryHeading}>{item.desc}</Typography>
                    </ExpansionPanelSummary>
                    {expanded === item.title?<ExpansionPanelDetails>{item.view}</ExpansionPanelDetails>:undefined}
                </ExpansionPanel>
            })}
        </div>
    }
};

export default withStyles(styles)(SwitchView);