import React from 'react';
import KView from './kview';
import { withStyles } from '@material-ui/core/styles';
import Paper from '@material-ui/core/Paper';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import RadioGroup from '@material-ui/core/RadioGroup';
import Radio from '@material-ui/core/Radio';
import FormControl from '@material-ui/core/FormControl';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import {CompanyContext} from './CompanyContext';

/**
 * 测试查看K日数据库是否正确
 */

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
        marginBottom:3*theme.spacing.unit
    }
  });

class KQuery extends React.Component{
    constructor(props){
        super(props);
        this.state = {range:1};
    }
    handeChangeRange(event,value){
        this.setState({range:value});
    }
    render(){
        const {classes} = this.props;
        let {range} = this.state;

        return <div>
                <Paper className={classes.paper}>
                    <FormControl component="fieldset">
                        <RadioGroup row name="range"  value={range} onChange={this.handeChangeRange.bind(this)}>
                            <FormControlLabel value={"1"} control={<Radio />} label="1年" />
                            <FormControlLabel value={"5"} control={<Radio />} label="5年" />
                            <FormControlLabel value={"10"} control={<Radio />} label="10年" />                    
                            <FormControlLabel value={"40"} control={<Radio />} label="全部" />                    
                        </RadioGroup>                    
                    </FormControl>
                </Paper>
                <KView width={'100%'} height={640} code={this.context.code} range={range}/>
            </div>;
    }
}

KQuery.contextType  = CompanyContext;

export default withStyles(styles)(KQuery)
