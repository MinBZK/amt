const path = require('path');

module.exports = {
  mode: 'development',
  entry: './amt/site/static/ts/amt.ts',
  output: {
    filename: 'amt.js',
    path: path.resolve(__dirname, 'amt/site/static/js'),
    publicPath: 'amt/site/static/js'
  },
  devtool: 'eval-cheap-source-map',
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: 'ts-loader',
        exclude: /node_modules/
      }
    ]
  },
  resolve: {
    extensions: ['.ts', '.js']
  }
};
