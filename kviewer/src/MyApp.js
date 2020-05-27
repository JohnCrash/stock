import React, { Component } from 'react';
import KView from './kview';
import { withStyles } from '@material-ui/core/styles';

const styles = theme => ({
    button: {
        margin: theme.spacing.unit,
      },
      textField: {
        marginLeft: theme.spacing.unit,
        marginRight: theme.spacing.unit,
        width: 200,
      },   
    paper:{
        marginBottom:3*theme.spacing.unit
    }
  });

class MyApp extends Component {
    constructor(props){
        super(props);
    }

    render(){
        const {classes} = this.props;

        return <div>
                <KView width={'100%'} height={920} code='SH000001' range={440}/>
            </div>;
    }    
}

export default withStyles(styles)(MyApp)
