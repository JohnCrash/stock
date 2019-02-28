import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import Tabs from '@material-ui/core/Tabs';
import Tab from '@material-ui/core/Tab';
import Typography from '@material-ui/core/Typography';
import MacdStandardView from './MacdStandardView';
import MacdCycleView from './MacdCycleView';
import MacdWideView from './MacdWideView';
import MacdComplexView from './MacdComplexView';

const ViewArray = [
    <MacdStandardView />,
    <MacdCycleView />,
    <MacdWideView />,
    <MacdComplexView />
];

class MacdView extends Component{
    constructor(props){
        super(props);
        this.state = {
            value: 0,
        };
    }
    handleChange(event,index){
        this.setState({ value: index });
    }
    render(){
        let {value} = this.state;

        return <div>
            <Tabs
                value={value}
                onChange={this.handleChange.bind(this)}
                indicatorColor="primary"
                textColor="primary"
                variant="fullWidth"
            >
                <Tab label="严格" />
                <Tab label="周期优化" />
                <Tab label="大盘优化" />
                <Tab label="综合优化" />
          </Tabs>
          {ViewArray[value]}
        </div>;
    }
}

export default MacdView;
