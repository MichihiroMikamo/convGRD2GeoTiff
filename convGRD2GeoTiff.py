"""
これはDEMファイル(.grd)をGeoTiffに変換し，
さらに，変換後の数値データに含まれるnanを0にするプログラム．
"""


from osgeo import gdal,ogr,osr
import subprocess
import numpy as np


import sys
import os
import pprint


# # gcal_calc.pyにパスを通す(そんな必要あるの?通っているべきではないのか?)
# import os
# sys.path.append(os.path.join(os.path.dirname(__file__), 'D:\mikamo\env_gdal\Scripts'))
# pprint.pprint(sys.path) # モジュールがpathに追加されているか確認する．


def ReprojectCoords(coords,src_srs,tgt_srs):
    """ Reproject a list of x,y coordinates. """
    trans_coords=[]
    transform = osr.CoordinateTransformation( src_srs, tgt_srs)
    for x,y in coords:
        x,y,z = transform.TransformPoint(x,y)
        trans_coords.append([x,y])
    return trans_coords


def main():
    ##########################
    ### これは試行錯誤の途中 ###
    ### 使わない ##############
    ##########################

    infilename = 'data/1673828005.133.114.248.69/1673828005.133.114.248.69_tmp/dem.grd'
    tempfilename = infilename.replace('.grd', '_temp.tif')
    cmd = 'gdal_translate -a_srs EPSG:4612 {0} {1}'.format(infilename, tempfilename)
    subprocess.run(cmd, shell=True)

    ###############################
    ### nanを0に変えたGeoTiffを得る
    ###############################
    src        = gdal.Open(tempfilename)
    src_array  = src.GetRasterBand(1).ReadAsArray()

    print('src_array = ', src_array)
    src_array2 = np.nan_to_num(src_array)
    print('src_array2 = ', src_array2)

    Metadata = src.GetMetadata() # メタデータの取り出し
    Projection = src.GetProjection() # Projectionの取り出し

    #ulx, xres, xskew, uly, yskew, yres  = src.GetGeoTransform()
    geoTransform  = src.GetGeoTransform()
    ulx   = geoTransform[0] # x-coordinate of the upper-left corner of the upper-left pixel.
    xres  = geoTransform[1] # w-e pixel resolution / pixel width.
    xskew = geoTransform[2] # row rotation (typically zero).
    uly   = geoTransform[3] # y-coordinate of the upper-left corner of the upper-left pixel.
    yskew = geoTransform[4] # column rotation (typically zero).
    yres  = geoTransform[5] # n-s pixel resolution / pixel height (negative value for a north-up image).

    lrx = ulx + (src.RasterXSize * xres) # 地図座標系 + 画像サイズ(width)  * x方向の解像度(ピクセルサイズ)
    lry = uly + (src.RasterYSize * yres) # 地図座標系 + 画像サイズ(height) * x方向の解像度(ピクセルサイズ)

    print('ulx = ', ulx) # 左上のx 地図座標系
    print('uly = ', uly) # 左上のy 地図座標系
    print('lrx = ', lrx) # 右下のx 地図座標系
    print('lry = ', lry) # 右下のy 地図座標系

    ext = []
    ext.append((ulx, uly))
    ext.append((lrx, uly))
    ext.append((ulx, lry))
    ext.append((lrx, lry))

    src_srs=osr.SpatialReference()
    src_srs.ImportFromWkt(src.GetProjection())
    tgt_srs = src_srs.CloneGeogCS()
    geo_ext = ReprojectCoords(ext, src_srs, tgt_srs)

    print('get_ext = ', geo_ext)


    #exit()
    height = src_array2.shape[0]
    width  = src_array2.shape[1]
    
    
    outfilename = tempfilename.replace('_temp.tif', '_new.tif') # 出力ファイル名
    numOfband = 1 # バンド数によって変える．DEMは1数値データ
    dtype = gdal.GDT_Float32
    output = gdal.GetDriverByName('GTiff').Create(outfilename, width, height, numOfband, dtype) # 空のファイル作成
    output.SetProjection(Projection) # Projectionの追加
    output.SetMetadata(Metadata) # メタデータの追加
    #output.SetGCPs(gcps, dsProjection) # GCPsの追加
    output.GetRasterBand(1).WriteArray(src_array2) # 画素値の追加
    output.FlushCache()

    ############################
    ### gdalinfoで確認する
    ############################
    cmd = 'gdalinfo {0}'.format(outfilename)
    subprocess.run(cmd, shell=True)

    print('\ndone.')



def main2():
    
    ###############################
    ### .grdファイルをGeoTiffに変換する
    ### (ここでは，数値データにnanが入っている)
    ###############################
    infilename = 'data/1673828005.133.114.248.69/1673828005.133.114.248.69_tmp/dem.grd'
    tempfilename = infilename.replace('.grd', '_temp.tif')
    cmd = 'gdal_translate -a_srs EPSG:4612 {0} {1}'.format(infilename, tempfilename)
    subprocess.run(cmd, shell=True)

    # 数値データを確認する
    out = gdal.Open(tempfilename)
    out_array = out.GetRasterBand(1).ReadAsArray()
    print('out_array0 = ', out_array)
    

    ###############################
    ### nanを0に変えたGeoTiffを得る
    ### (ここではProjectionが無くなっている)
    ###############################
    temp2filename = tempfilename.replace('_temp.tif', '_temp2.tif')
    cmd = 'python D:/mikamo/env_gdal/Scripts/gdal_calc.py -A {0} --calc="nan_to_num(A)" --outfile={1} --NoDataValue=0'.format(infilename, temp2filename)
    subprocess.run(cmd, shell=True)

    # 数値データを確認する
    out = gdal.Open(temp2filename)
    out_array = out.GetRasterBand(1).ReadAsArray()
    print('out_array2 = ', out_array)

    ###############################
    ### projectionを追加する
    ###############################
    outfilename = temp2filename.replace('_temp2.tif', '_temp3.tif')
    cmd = 'gdal_translate -of "GTiff" -co "COMPRESS=LZW" -a_srs WGS84 {0} {1}'.format(temp2filename, outfilename) # WGS84で良いのかは不明．
    subprocess.run(cmd, shell=True)

    # 数値データを確認する
    out = gdal.Open(outfilename)
    out_array = out.GetRasterBand(1).ReadAsArray()
    print('out_array3 = ', out_array)


    ############################
    ### gdalinfoで確認する
    ############################
    cmd = 'gdalinfo {0}'.format(outfilename)
    subprocess.run(cmd, shell=True)


    print('\ndone.')


def main3():

    ###############################
    ### .grdファイルをGeoTiffに変換する
    ### (ここでは，数値データにnanが入っている)
    ###############################
    infilename = 'data/1673828005.133.114.248.69/1673828005.133.114.248.69_tmp/dem.grd'
    tempfilename = infilename.replace('.grd', '_temp.tif')
    cmd = 'gdal_translate -a_srs EPSG:4612 {0} {1}'.format(infilename, tempfilename)
    subprocess.run(cmd, shell=True)

    # 数値データを確認する
    out = gdal.Open(tempfilename)
    out_array = out.GetRasterBand(1).ReadAsArray()
    print('out_array0 = ', out_array)
    

    src = gdal.Open(tempfilename)
    temp_vrt = gdal.Translate('', src, format="MEM", bandList=[1], outputType=gdal.GDT_Float32, resampleAlg=gdal.GRA_Cubic) # 三鴨修正
    data = src.GetRasterBand(1).ReadAsArray()

    #############################
    ### nanを0に設定する 
    #############################
    dataZero = np.nan_to_num(data)

    temp_vrt.GetRasterBand(1).WriteArray(dataZero)
    temp_vrt.GetRasterBand(1).SetNoDataValue(0) # 0は黒ではなく透過で表示されるようにする．
    #temp_vrt.BuildOverviews("CUBIC", check_factor(temp_vrt.RasterXSize, temp_vrt.RasterYSize))
    temp_vrt.BuildOverviews("CUBIC", [2,4,8,16,32,64]) # 三鴨修正
    temp_vrt.FlushCache()

    outfilename = tempfilename.replace('_temp.tif', '_temp2.tif')
    dst = gdal.GetDriverByName('Gtiff').CreateCopy(outfilename,temp_vrt,options=["COPY_SRC_OVERVIEWS=YES","TILED=YES","COMPRESS=LZW"])
    temp_vrt = None
    dst.FlushCache()

    # 数値データを確認する
    out = gdal.Open(outfilename)
    out_array = out.GetRasterBand(1).ReadAsArray()
    print('out_array1 = ', out_array)


    print('done')


if __name__=='__main__':
    main3()
    