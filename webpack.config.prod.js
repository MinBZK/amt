const path = require('path');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const HtmlWebpackDeployPlugin = require("html-webpack-deploy-plugin");

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
    new HtmlWebpackDeployPlugin({
      usePackagesPath: false,
      packages: {
        '@nl-rvo/assets': {
          copy: [
            { from: 'fonts', to: 'fonts/'},
            { from: 'icons', to: 'icons/'},
            { from: 'images', to: 'images/'}
          ],
          links: [
            'fonts/index.css',
            'icons/index.css',
            'images/index.css',
          ]
        },
        '@nl-rvo/design-tokens': {
          copy: [
            { from: 'dist/index.css', to: 'index.css' },
            { from: 'dist/index.js', to: 'index.js' },
          ],
          links: [
            'index.css',
          ],
          scripts: [
            'index.js',
          ]
        },
        '@nl-rvo/component-library-css': {
          copy: [
            { from: 'dist/index.css', to: 'index.css' },
          ],
          links: [
            'index.css',
          ]
        },
      }
    }),
    new MiniCssExtractPlugin({
      filename: "[name].[contenthash].css",
      chunkFilename: "[id].css",
    }),
  ]
};
