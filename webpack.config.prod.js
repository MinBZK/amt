const path = require('path');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {
  mode: 'production',
  entry: './amt/site/static/ts/amt.ts',
  output: {
    filename: 'amt.[contenthash].js',
    path: path.resolve(__dirname, 'amt/site/static/dist'),
    clean: true,
    publicPath: '/static/dist/'
  },
  devtool: 'source-map',
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: 'ts-loader',
        exclude: /node_modules/
      },
      {
        test: /\.s[ac]ss$/i,
        use: [
          MiniCssExtractPlugin.loader,
          "css-loader",
          {
            loader: "sass-loader",
            options: {
              sourceMap: true,
              sassOptions: {
                outputStyle: "compressed",
              },
            },
          },
        ],
      },
    ]
  },
  resolve: {
    extensions: ['.ts', '.js']
  },
  plugins: [
    new CleanWebpackPlugin(),
    new HtmlWebpackPlugin({
      template: 'amt/site/templates/layouts/base.html.j2.webpack',
      filename: path.resolve(__dirname, 'amt/site/templates/layouts/base.html.j2'),
      inject: false
    }),
    new MiniCssExtractPlugin({
      filename: "[name].[contenthash].css",
      chunkFilename: "[id].css",
    }),
  ]
};
