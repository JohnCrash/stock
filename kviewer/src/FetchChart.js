import React, { Component } from 'react';
import EChart from './echart';
import {postJson} from './fetch';

class FetchChart extends Component{
    constructor(props){
        super(props);  
        this.state = {options:{}};
    }
    componentWillUpdate(nextProps, nextState, snapshot){
        if(nextProps.api!==this.props.api||nextProps.args!==this.props.args||nextProps.init!=this.props.init)
            this.initComponent(nextProps);
    }
    componentDidMount(){
        this.initComponent(this.props);
    }
    initComponent(props){
        postJson(props.api,props.args,(json)=>{
            if(json.results){
                this.setState({options:props.init(json)});
            }else{
                console.error(json.error);
            }
        });
    }   
    render(){
        let {width,height} = this.props
        return <EChart options={this.state.options} width={width} height={height}/>;
    }
}

export default FetchChart;