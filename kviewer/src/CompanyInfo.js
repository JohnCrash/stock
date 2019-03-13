import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import {postJson} from './fetch';
import {CompanyContext} from './CompanyContext';
import {assign,isEqual} from 'lodash';
import Typography from '@material-ui/core/Typography';
import Paper from '@material-ui/core/Paper';

const styles = theme => ({
    root: {
        width:'100%'
      },
    paper: {
        margin:theme.spacing.unit
    }
});

class CompanyInfo extends Component{
    constructor(props){
        super(props);
        this.oldContext = {};
        this.state = {
            text:''
        }
    }
    componentDidUpdate(prevProps, prevState, snapshot){
        this.initComponent(this.props);
    }
    componentDidMount(){
        this.initComponent(this.props);
    }
    initComponent(props){
        if(!this.context.code || isEqual(this.oldContext,this.context)){
            return;
        }
        assign(this.oldContext,this.context);

        postJson('/api/desc',{code:this.context.code},(json)=>{
            if(json.results && json.results.length==1){
                this.setState({text:json.results[0].business});
            }else{
                console.error(json.error);
            }
        });            
    }   
    render(){
        let {classes} = this.props;
        let {text} = this.state;
        return <Paper className={classes.paper}>
            <Typography variant="h5" component="h3">
                主营业务
            </Typography>
            <Typography>
                {text}
            </Typography>
        </Paper>
    }
}

CompanyInfo.contextType = CompanyContext;

export default withStyles(styles)(CompanyInfo);