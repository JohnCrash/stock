import React, { Component } from 'react';
import EChart from './echart';
import {postJson} from './fetch';
import async from 'async';
import {Eq} from './kits';

class FetchChart extends Component{
    constructor(props){
        super(props);  
        this.state = {options:{}};
    }
    componentWillUpdate(nextProps, nextState, snapshot){
        if(!Eq(nextProps.api,this.props.api)||!Eq(nextProps.args,this.props.args)){
            this.initComponent(nextProps);
        }
    }
    componentDidMount(){
        this.initComponent(this.props);
    }
    initComponent(props){
        if(props.api instanceof Array){
            let tasks = [];
            props.api.forEach(api => {
                tasks.push((cb)=>{
                    postJson(api,props.args,(json)=>{
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
            postJson(props.api,props.args,(json)=>{
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

export default FetchChart;