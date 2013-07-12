class Record():
    
    records = [] #recordID datasetID Re totalSLPM phi airSLPM fuelSLPM pressure temperature time date   
    sets = []

    
    def __init__(self, flow_, ui_):
        self.flow = flow_
        self.ui = ui_
        self.current_record = 0
        self.current_set = 0
        self.record_ID = 0
        self.set_ID = 0
        self.set_counter = 0
        self.record_counter = 0
        self.selected_item = QtGui.QTreeWidgetItem()


    def new_record(self):
        self.record_ID += 1
        self.set_ID = self.current_set
        record_list = [str(self.record_ID),
                        str(self.set_ID),
                        str(self.flow.get_Reynolds_flow()),
                        str(self.flow.get_phi_flow()),
                        str(self.flow.get_totalMassFlow()),
                        str(self.flow.get_airMassFlow()),
                        str(self.flow.get_fuelMassFlow()),
                        str(self.flow.get_power()),
                        str(self.flow.get_mean_velocity()),
                        str(self.flow.get_air_meter_pressure()),
                        str(self.flow.get_air_meter_temperature()),
                        str(time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())),
                        self.ui.comments_textBox.toPlainText()]
        self.records.append(record_list)
        return record_list

    def dataset_average_field(self, dataset_id, average_field):
        dataset_records = self.sort_dataset(self.records, 1, str(dataset_id))
        average = 0
        for i in range(len(dataset_records)):
            average = average + float(dataset_records[i][average_field])
        return str(average / len(dataset_records))    

    def add_record(self):
        new_record = self.new_record()
        print self.records
        print self.current_set
        new_list_item = QtGui.QTreeWidgetItem(self.sets[self.current_set-1][1],new_record)
        self.update_dataset_averages(self.current_set)
        self.set_dataset_setText(self.current_set)
        

    def update_dataset_averages(self, dataset_id):
        print 'dataset id ' + str(dataset_id)
        self.sets[dataset_id-1][2] = self.dataset_average_field(dataset_id, 2)
        self.sets[dataset_id-1][3] = self.dataset_average_field(dataset_id, 3)
        self.sets[dataset_id-1][4] = self.dataset_average_field(dataset_id, 4)
        self.sets[dataset_id-1][5] = self.dataset_average_field(dataset_id, 5)
        self.sets[dataset_id-1][6] = self.dataset_average_field(dataset_id, 6)
        self.sets[dataset_id-1][7] = self.dataset_average_field(dataset_id, 7)
        self.sets[dataset_id-1][8] = self.dataset_average_field(dataset_id, 8)
        self.sets[dataset_id-1][9] = self.dataset_average_field(dataset_id, 9)
        self.sets[dataset_id-1][10] = self.dataset_average_field(dataset_id, 10)
        

    def new_record_set(self):
        self.set_counter += 1
        self.current_set = self.set_counter
        new_set_item = QtGui.QTreeWidgetItem(self.ui.record_list)
        set_data = [self.current_set, new_set_item,'-','-','-','-','-','-','-','-','-']
        self.sets.append(set_data)
        self.set_dataset_setText(self.current_set)
        self.ui.record_list.setCurrentItem(new_set_item)

    def set_dataset_setText(self, dataset_id):
        self.sets[dataset_id-1][1].setText(0, 'set ' + str(self.sets[dataset_id-1][0]))
        self.sets[dataset_id-1][1].setText(2, self.sets[dataset_id-1][2]) #Reynolds
        self.sets[dataset_id-1][1].setText(3, self.sets[dataset_id-1][3]) #phi
        self.sets[dataset_id-1][1].setText(4, self.sets[dataset_id-1][4]) #totalMassFlow
        self.sets[dataset_id-1][1].setText(5, self.sets[dataset_id-1][5]) #airSLPM
        self.sets[dataset_id-1][1].setText(6, self.sets[dataset_id-1][6]) #fuelSLPM
        self.sets[dataset_id-1][1].setText(7, self.sets[dataset_id-1][7]) #power
        self.sets[dataset_id-1][1].setText(8, self.sets[dataset_id-1][8]) #mean_velocity
        self.sets[dataset_id-1][1].setText(9, self.sets[dataset_id-1][9]) #pressure
        self.sets[dataset_id-1][1].setText(10, self.sets[dataset_id-1][10]) #temperature    

    def delete_record(self):
        if self.isRecord:
            print 'Item is child. Deleteing selected child.'
            #delete child item
            self.records.pop(self.search_list(self.records,0,self.selected_item.text(0)))
            self.selected_item.removeChild(self.selected_item)
            del self.selected_item
        if self.dataset_isEmpty(self.current_set):
            self.sets[self.current_set-1][2:] = ['-','-','-','-','-','-','-']
            self.set_dataset_setText(self.current_set)          
            
    def set_current_record(self):
        self.selected_item = self.ui.record_list.currentItem()
        if self.selected_item == None:
            self.isRecord = False
        elif self.selected_item.parent() == None:
            print 'Item is a parent.'
            print self.selected_item.text(0)
            dummy = self.selected_item.text(0).split(' ')
            self.current_set = int(dummy[1])
            self.isRecord = False
        else:
            print 'Item is a child.'
            print self.selected_item.text(0) + ' from set ' + self.selected_item.text(1)
            self.current_set = int(self.selected_item.text(1))
            self.current_record = int(self.selected_item.text(0))
            self.isRecord = True 

    def search_list(self, source_list, search_field, search_value):
        index = 0
        for index , s_list in enumerate(source_list):
            if s_list[search_field] == search_value:
                print 'deleting item with index ' + str(index)
                print s_list
                return index
                print 'breaking'
                break

    def sort_dataset(self, source_list, search_field, search_value):
        index = 0
        sorted_list = []
        for index, s_list in enumerate(source_list):
            if s_list[search_field] == search_value:
                sorted_list.append(s_list)
        return sorted_list

    def dataset_isEmpty(self, dataset_id):
        dataset_records = self.sort_dataset(self.records,1,str(dataset_id))
        if len(dataset_records) == 0:
            print 'dataset is empty'
            return True
        else:
            return False


    def save_to_file(self):
        file_date = time.strftime("%a_%d_%b_%Y_%Hh%Mm%Ss", time.localtime())
        #Sets
        file_name = 'sets_ ' + file_date
        file_datasets = open(file_name, 'w')
        file_datasets.write('# datasetID Re phi total_massflow air_massflow fuel_massflow power mean_velocity pressure temperature\n')
        for i in range(len(self.sets)):
            file_datasets.write(str(self.sets[i][0]) + ' ' + self.sets[i][2] + ' ' +
                                self.sets[i][3] + ' ' + self.sets[i][4] + ' ' + self.sets[i][5] + ' ' +
                                self.sets[i][6] + ' ' + self.sets[i][7] + ' ' + self.sets[i][8] + ' ' +
                                self.sets[i][9] + ' ' + self.sets[i][10] + '\n')
        file_datasets.close()
        #Records
        file_name = 'records_ ' + file_date
        file_records = open(file_name, 'w')
        file_records.write('record# Re phi totalSLPM airSLPM fuelSLPM power mean_velocity pressure temperature date comments\n')
        for i in range(len(self.records)):
            file_records.write(str(self.records[i][0]) + self.records[i][1] + ' ' + self.records[i][2] + ' ' +
                                self.records[i][3] + ' ' + self.records[i][4] + ' ' + self.records[i][5] + ' ' +
                                self.records[i][6] + ' ' + self.records[i][7] + ' ' + self.records[i][8] + ' ' +
                                self.records[i][9] + ' ' + self.records[i][10] + ' ' +
                                self.records[i][11] + ' ' + self.records[i][12] + '\n')
        file_records.close()

    def clear_records(self):
        self.sets = []
        self.records =  []
        self.ui.record_list.clear()


#################################### end of class Record ####################################
