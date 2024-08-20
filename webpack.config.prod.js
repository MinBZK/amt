const path = require('path');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');

module.exports = {
  mode: 'production',
  entry: './amt/site/static/ts/amt.ts',
  output: {
    filename: 'amt.[contenthash].js',
    path: path.resolve(__dirname, 'amt/site/static/js'),
    publicPath: 'amt/site/static/js'
  },
  devtool: 'source-map',
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
  },
  plugins: [
    new CleanWebpackPlugin()
  ]
};
