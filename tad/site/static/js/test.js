window.onload = function() {
  console.log("This test file has been loaded");

  var columnTodo = document.getElementById('column-todo');
  var columnInProgress = document.getElementById('column-in-progress');

  new Sortable(columnTodo, {
    group: 'shared', // set both lists to same group
    animation: 150
  });

  new Sortable(columnInProgress, {
    group: 'shared',
    animation: 150
  });


}
