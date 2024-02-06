exports.Task = extend(TolokaHandlebarsTask, function (options) {
    TolokaHandlebarsTask.call(this, options);
  }, {
    onRender: function() {
      //Define variables
      var $root = $(this.getDOMElement());
      var _this = this;
          
      var solution = TolokaHandlebarsTask.prototype.getSolution.apply(this, arguments);
  
      $root.on('change', '.least', function(){
        var result = $(this).val()
        _this.setSolutionOutputValue('least', result);
        return solution;
      }) 
  
      $root.on('change', '.most', function(){
        var result = $(this).val()
        _this.setSolutionOutputValue('most', result);
        return solution;
      })
  
      var leastRadioArr = this.getDOMElement().querySelectorAll('.least')
      leastRadioArr.forEach(element => element.name = "Least-" + this.getOptions().taskIndex)
  
      var mostRadioArr = this.getDOMElement().querySelectorAll('.most')
      mostRadioArr.forEach(element => element.name = "Most-" + this.getOptions().taskIndex)
    },
    onDestroy: function() {
      // _TANKER_TRANSLATE_prj:default:ondestroy 
    }
  });
  
  function extend(ParentClass, constructorFunction, prototypeHash) {
    constructorFunction = constructorFunction || function () {};
    prototypeHash = prototypeHash || {};
    if (ParentClass) {
      constructorFunction.prototype = Object.create(ParentClass.prototype);
    }
    for (var i in prototypeHash) {
      constructorFunction.prototype[i] = prototypeHash[i];
    }
    return constructorFunction;
  }