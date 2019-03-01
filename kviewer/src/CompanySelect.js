import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import TextField from '@material-ui/core/TextField';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import Button from '@material-ui/core/Button';
import Snackbar from '@material-ui/core/Snackbar';
import CompanySelectTable from './CompanySelectTable';
import {postJson} from './fetch';
import {dateString} from './kits';

const styles = theme => ({ 
});

/**
 * 用于选择股票和时间范围以及其他参数
 */

 class CompanySelect extends Component{
    state = {
        companys : [],
        openbar : false,
        err : 'hello'
    };
    handleInput=(event)=>{
        if(event.key==='Enter'){
            postJson('/api/select',{cmd:event.target.value},(json)=>{
                if(json.error){
                    this.setState({openbar:true,err:json.error});
                }else{
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
                }
            });
        }
    };
    handleCloseSnackbar=(event)=>{
        this.setState({ openbar: false });
    };
    render(){
        const { classes,onClose } = this.props;
        const { companys,openbar,err} = this.state;
        return (
              <Dialog
                fullWidth={true}
                maxWidth={'xl'}
                open={this.props.open}
                onClose={onClose}
                aria-labelledby="form-dialog-title"
              >
                <DialogTitle id="form-dialog-title">股票选择</DialogTitle>
                <DialogContent>
                  <DialogContentText>
                      输入股票名称或者代码，也可以以#开头输入一个数据库查询条件。
                  </DialogContentText>
                  <TextField
                    autoFocus
                    margin="dense"
                    id="name"
                    fullWidth
                    onKeyPress={this.handleInput}
                  />
                  <CompanySelectTable data={companys}/>
                </DialogContent>
                <DialogActions>
                <TextField
                        id="date"
                        label="起始日期"
                        type="date"
                        defaultValue="2017-05-24"
                        className={classes.textField}
                        InputLabelProps={{
                        shrink: true,
                        }}
                    />
                    <TextField
                        id="date"
                        label="结束日期"
                        type="date"
                        defaultValue="2017-05-24"
                        className={classes.textField}
                        InputLabelProps={{
                        shrink: true,
                        }}
                    />                     
                  <Button onClick={onClose} color="primary">
                    取消
                  </Button>
                  <Button onClick={onClose} color="primary">
                    确定
                  </Button>
                </DialogActions>
                <Snackbar
                    open={openbar}
                    onClose={this.handleCloseSnackbar}
                    ContentProps={{
                        'aria-describedby': 'message-id',
                    }}
                    message={<span id="message-id">${err}</span>}
                    />
              </Dialog>
          );
    }
 };

 export default withStyles(styles)(CompanySelect);