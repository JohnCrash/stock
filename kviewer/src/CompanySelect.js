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
 * prop.title标题
 * prop.lists选择列表
 * prop.search是否打开搜索栏
 */
 class CompanySelect extends Component{
    state = {
        companys : [],
        openbar : false,
        err : 'hello'
    };
    handleInput=(event)=>{
        if(event.key==='Enter'){
          this.requestSelect(event.target.value);
        }
    };
    handleCloseSnackbar=(event)=>{
        this.setState({ openbar: false });
    };
    handleCloseDialog=(result,args)=>()=>{
        this.props.onClose(result,args);
    };
    requestSelect(cmd){
      postJson('/api/select',{cmd},json=>{
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
    render(){
        const { classes,onClose,title,lists,search } = this.props;
        const { companys,openbar,err} = this.state;
        return (
              <Dialog
                fullWidth={true}
                maxWidth={'xl'}
                open={this.props.open}
                onClose={this.handleCloseDialog('cancel')}
                aria-labelledby="form-dialog-title"
              >
                <DialogTitle id="form-dialog-title">{title?title:'股票选择'}</DialogTitle>
                <DialogContent>
                  {search?[<DialogContentText>
                      输入股票名称或者代码，也可以以#开头输入一个数据库查询条件。
                    </DialogContentText>,
                    <TextField
                      autoFocus
                      margin="dense"
                      id="name"
                      fullWidth
                      onKeyPress={this.handleInput}/>]:undefined}
                  <CompanySelectTable data={lists?lists:companys}/>
                </DialogContent>
                <DialogActions>                   
                  <Button onClick={this.handleCloseDialog('cancel')} color="primary">
                    取消
                  </Button>
                  <Button onClick={this.handleCloseDialog('ok',companys)} color="primary">
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