import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import {dateString,getDayLength,days} from './kits';
import FetchChart from './FetchChart';
import GameChart from './GameChart';
import Button from '@material-ui/core/Button';
import Chip from '@material-ui/core/Chip';
import AttachMoneyIcon from '@material-ui/icons/AttachMoney';
import Typography from '@material-ui/core/Typography';

const upColor = '#ec0000';
const upBorderColor = '#ec0000';
const downColor = '#00da3c';
const downBorderColor = '#008F28';
const goldColor = '#ffd54f';
const buyColor = '#7c4dff';

const styles = theme => ({
    root: {
        width:'100%'     
    },
    graph:{
        width:'100%',
        display:'flex',

    },
    button: {
        margin: theme.spacing.unit
    },
    clip: {
        margin: theme.spacing.unit,
        primaryColor:{
            backgroundColor:'#00FF00',
            color:'#00FF00'
        }
    },
    control:{
        width:'100%',
        display:'flex',
        justifyContent:"center",
        flexWrap:"wrap"
    }   
  });

function p100(d){
    return Math.floor(d*10000)/10000;
}
class GameView extends Component{
    constructor(props){
        super(props);
    }
    state={
        value:1.0,
        num:1,
        rand:Math.random(),
        BuyValue:0,
        SellValue:0,
        days:0,
        disableBuy:false,
        disableSell:true
    }
    handleBuy=()=>{
        let d = this.stock.cur();
        //d.date; //买入日期
        this.setState({disableSell:true,disableBuy:true,BuyValue:p100(d.value[1])}); //买入价
    }
    handleSell=()=>{
        let d = this.stock.cur();
        let SellValue = d.value[1];
        let BuyValue = p100(this.state.BuyValue);
        this.setState({SellValue:0,
            BuyValue:0,
            value:p100(this.state.value*SellValue/BuyValue-0.003),
            num:this.state.num+1,
            disableBuy:false,
            disableSell:true
        });
    }
    handleNext=()=>{
        this.stock.next(this.state.BuyValue);
        this.sh000001.next();
        if(this.state.BuyValue>0)
            this.setState({disableSell:false,disableBuy:true,days:this.state.days+1});
        else
            this.setState({days:this.state.days+1});
    }
    /**
     * 弹出对话栏，根据条件卖出或者买入
     */
    handleNextIF=()=>{
        this.stock.next(this.state.BuyValue);
        this.sh000001.next();
        if(this.state.BuyValue>0)
            this.setState({disableSell:false,disableBuy:true,days:this.state.days+1});
        else
            this.setState({days:this.state.days+1});
    }
    callback=(key)=>(self)=>{
        this[key]= self;
    }
    render(){
        let {value,num,rand,BuyValue,SellValue,disableBuy,disableSell,days} = this.state;
        let {classes} = this.props;
        return <div className={classes.root}>
            <div className={classes.graph}>
                <GameChart width="100%" rand={rand} args={{code:"SH000001"}} height={860} thisCallBack={this.callback('sh000001')}/>
                <GameChart width="100%" rand={rand} height={860} thisCallBack={this.callback('stock')}/>
            </div>
            <div className={classes.control}>
                <Button className={classes.button} variant="contained" disabled={disableBuy?true:false} color="secondary" onClick={this.handleBuy.bind(this)}>
                    买入
                </Button>
                <Button className={classes.button} variant="contained" disabled={disableSell?true:false} color="secondary" onClick={this.handleSell.bind(this)}>
                    卖出
                </Button>
                <Button className={classes.button} variant="contained" color="primary" onClick={this.handleNext.bind(this)}>
                    下一天
                </Button>
                <Button className={classes.button} variant="contained" color="primary" onClick={this.handleNextIF.bind(this)}>
                    下一天条件交易
                </Button>
                <Typography variant="h3" >
                    收益率: {value} 买入价: {BuyValue}
                </Typography>
                <Typography variant="h3">
                    交易次数: {num} 用时:{days}天
                </Typography>
            </div>
        </div>
    }
}

export default withStyles(styles)(GameView);

