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
    render(){
        const {classes} = this.props;

        return <div>
                <KView width={'100%'} height={920} code={this.context.code} range={this.context.range}/>
            </div>;
    }
}

KQuery.contextType  = CompanyContext;

export default withStyles(styles)(KQuery)
