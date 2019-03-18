import React, { Component } from 'react';
import EChart from './echart';
import {postJson} from './fetch';
import async from 'async';
import {CompanyContext} from './CompanyContext';
import {assign,isEqual} from 'lodash';

class FetchChart extends Component{
    constructor(props){
        super(props);  
        this.state = {options:{}};
        this.args = {};
        this.oldContext = {};
        this.oldArgs = {};
    }
    componentDidUpdate(prevProps, prevState, snapshot){
        this.initComponent(this.props);
    }
    componentDidMount(){
        this.initComponent(this.props);
    }
    initComponent(props){
        if(!this.context.code || 
            (isEqual(this.oldContext,this.context) && isEqual(this.api,props.api) && isEqual(this.oldArgs,props.args?props.args:{}))){
            return;
        }
        let args = {};
        assign(this.oldContext,this.context);
        assign(this.oldArgs,props.args);
        this.api = props.api;
        //将props.args追加到args传送给fetch
        assign(args,this.context);
        assign(args,props.args);

        if(this.api instanceof Array){
            let tasks = [];
            this.api.forEach(api => {
                tasks.push((cb)=>{
                    postJson(api,args,(json)=>{
                        cb(json.error,json);
                    });
                })
            });
            async.parallel(tasks,(err,a)=>{
                if(err)
                    console.error(err);
                else
                    this.setState({options:props.init(a)});
            });
        }else{
            postJson(this.api,args,(json)=>{
                if(json.results){
                    this.setState({options:props.init(json)});
                }else{
                    console.error(json.error);
                }
            });            
        }
    }   
    render(){
        let {width,height} = this.props
        return <EChart options={this.state.options} width={width} height={height} {...this.props}/>;
    }
}

FetchChart.contextType = CompanyContext;
export default FetchChart;