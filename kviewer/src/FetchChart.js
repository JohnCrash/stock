import React, { Component } from 'react';
import EChart from './echart';
import {postJson} from './fetch';
import async from 'async';
import {Eq} from './kits';
import {CompanyContext} from './CompanyContext';

class FetchChart extends Component{
    constructor(props){
        super(props);  
        this.state = {options:{}};
        this.args = {};
    }
    componentDidUpdate(prevProps, prevState, snapshot){
        this.initComponent(this.props);
    }
    componentDidMount(){
        this.initComponent(this.props);
    }
    initComponent(props){
        if(!this.context.code || 
            (this.args.range===this.context.range && this.args.code===this.context.code && Eq(this.args.selects,this.context.selects) && Eq(this.api,props.api))){
            return;
        }
            
        this.args.code = this.context.code;
        this.args.selects = this.context.selects;
        this.args.range = this.context.range;
        this.api = props.api;

        if(this.api instanceof Array){
            let tasks = [];
            this.api.forEach(api => {
                tasks.push((cb)=>{
                    postJson(api,this.args,(json)=>{
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
            postJson(this.api,this.args,(json)=>{
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
        return <EChart options={this.state.options} width={width} height={height}/>;
    }
}

FetchChart.contextType = CompanyContext;
export default FetchChart;