import React,{Component} from 'react';
/*global echarts*/
class EChart extends Component{
    constructor(props){
        super(props);  
    }
    componentDidMount(){
        this.chart = echarts.init(this.node);
    }
    componentDidUpdate(nextProps, nextState, snapshot){
        if(nextProps.options!==this.props.options){
            this.chart.setOption(this.props.options); 
        }
    }
    render(){
        let {width,height} = this.props;
        return <div ref={ref=>this.node=ref} style={{width,height}}></div>;
    }
}

export default EChart;