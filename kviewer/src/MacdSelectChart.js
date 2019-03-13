import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import CompanySelectTable from './CompanySelectTable';
import {postJson} from './fetch';
import {dateString} from './kits';
import Button from '@material-ui/core/Button';

const styles = theme => ({
    root: {
        width:'100%'
      },
    button: {
        margin:theme.spacing.unit
    }
});

class MacdSelectView extends Component{
    state = {
        companys : []
    };
    componentDidMount(){
        let {day,buy} = this.props;
        postJson('/api/macdselect',{day,buy},json=>{
            let companys = [];
            let counter = 0;
            for(let v of json.results){
                counter++;
                let date = dateString(new Date(v.kbegin));
                companys.push({id:counter,
                    name:v.name,
                    code:v.code,
                    category:v.category?v.category:'',
                    date:date?date:'',
                    income:v.income,
                    static:v.static_income,
                    positive:v.positive_num,
                    negative:v.negative_num});
            }
            this.setState({companys});            
        });
    }
    handleXueqiu=()=>{
    }
    handleCollection=()=>{

    }
    render(){
        let {companys} = this.state;
        let {classes} = this.props;
        return <div className={classes.root}>
                <CompanySelectTable data={companys}/>
            </div>;
    }
}

export default withStyles(styles)(MacdSelectView);