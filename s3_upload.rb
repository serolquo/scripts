require './s3_upload_config'

#mime
MIMES = {
  '.txt'=>'text/plain',
  '.html'=>'text/html',
  '.jpg'=>'image/jpeg',
  '.png'=>'image/png'}

directories = [ROOT_DIR]  
  
while true do
  dir = directories.pop
    Dir.foreach (dir) do |item|
    next if item == '.' or item == '..' or IGNORE_FILES.include?(item)
    full_path_item = dir+'/'+item 
    if File.directory? full_path_item
      directories << full_path_item 
    else
      s3_key = full_path_item.clone
      s3_key.slice!(ROOT_DIR+'/')
      obj = BUCKET.object(s3_key)
      if !obj.exists?
        puts 'uploading new file: '+full_path_item
        obj.upload_file(full_path_item, 
          :content_type => MIMES[File.extname(full_path_item)], 
          :metadata=>{:tag => Digest::MD5.hexdigest(File.read full_path_item)})
      else #obj already there, do checksum check
        if obj.metadata['tag'] != (Digest::MD5.hexdigest File.read full_path_item)
          puts obj.metadata['tag']
          puts Digest::MD5.hexdigest File.read full_path_item
          puts 'uploading changed file: '+full_path_item
          obj.upload_file(full_path_item, 
            :content_type => MIMES[File.extname(full_path_item)], 
            :metadata=>{:tag => Digest::MD5.hexdigest(File.read full_path_item)})
        end
      end

    end
  end
  break if directories.empty?
end

puts 'done'

